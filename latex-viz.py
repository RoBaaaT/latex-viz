#!/usr/bin/env python3

import argparse
import glob
import io
import math
import os
import shutil
import subprocess
import tarfile

import ffmpeg
from PyPDF2 import PdfFileReader
from pdf2image import convert_from_path
from PIL import Image

def main(path, framerate, target_width, target_aspect_ratio):
    working_dir = path
    tmp_dir = os.path.join(working_dir, 'latex-viz-tmp')
    pdf_dir = os.path.join(working_dir, 'latex-viz-pdfs')
    img_dir = os.path.join(working_dir, 'latex-viz-imgs')
    if not os.path.isdir(path):
        print('Error: The specified path does not exist or is not a directory.')
        return
    if not os.path.isdir(pdf_dir):
        os.makedirs(pdf_dir)
    if not os.path.isdir(img_dir):
        os.makedirs(img_dir)

    # get commit history
    git_p = subprocess.run(['git', '-C', path, '--no-pager', 'log', '--pretty=format:%H', '--reverse'], capture_output=True)
    if git_p.returncode != 0:
        print('Error: Failed to get a commit history.')
        print(git_p.stderr.decode())
        return
    commits = git_p.stdout.decode().splitlines()
    print(f'Found {len(commits)} commits')

    # generate PDFs
    print('Generating PDFs...')
    for i, commit in enumerate(commits):
        pdf_path = os.path.join(pdf_dir, f'{i}-{commit}.pdf')
        if os.path.exists(pdf_path):
            print(f'PDF for commit {i + 1}/{len(commits)} already exists. Skipping.')
            continue
        git_p = subprocess.run(['git', '-C', path, 'archive', '--format=tar', commit], capture_output=True)
        if git_p.returncode != 0:
            print(f'Error: Failed to checkout commit {commit}.')
            print(git_p.stderr.decode())
            return

        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.makedirs(tmp_dir)
        with tarfile.open(fileobj=io.BytesIO(git_p.stdout)) as tar:
            tar.extractall(tmp_dir)

        print(f'Running latexmk for commit {i + 1}/{len(commits)} ({commit}).')
        latexmk_p = subprocess.run(['latexmk', '-interaction=nonstopmode', '-pdf'], cwd=tmp_dir, capture_output=True)
        if latexmk_p.returncode != 0:
            print('Warning: latexmk finished with errors, still checking for an output PDF.')
        pdf_paths = glob.glob(os.path.join(tmp_dir, '*.pdf'))
        if len(pdf_paths) == 0:
            print('Warning: Cannot find the generated PDF, skipping this commit.')
            continue
        shutil.copyfile(pdf_paths[0], pdf_path)

    # remove the tmp directory
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    max_page_count = 0
    page_aspect_ratio = None
    for i, commit in enumerate(commits):
        pdf_path = os.path.join(pdf_dir, f'{i}-{commit}.pdf')
        if not os.path.exists(pdf_path):
            continue
        with open(pdf_path, 'rb') as f:
            pdf = PdfFileReader(f)
            page_count = pdf.getNumPages()
            if page_count > max_page_count:
                max_page_count = page_count
            if page_aspect_ratio == None and page_count > 0:
                mbox = pdf.getPage(0).mediaBox
                page_aspect_ratio = float(mbox.getWidth() / mbox.getHeight())
    if max_page_count == 0:
        print('Error: All generated PDFs seem to be empty')
        return
    print(f'The maximum page count is {max_page_count} and the page aspect ratio is {page_aspect_ratio:.2f}.')

    # determine which grid we are going to use to arrange the pages
    row_count = 1
    while math.ceil(max_page_count / row_count) * page_aspect_ratio / row_count > target_aspect_ratio:
        row_count += 1
    col_count = math.ceil(max_page_count / row_count)
    aspect_ratio = col_count * page_aspect_ratio / row_count
    print(f'Using a {col_count}x{row_count} (aspect ratio {aspect_ratio:.2f}) grid to visualize the PDF pages.')

    # create the preview images
    img_width = math.floor(target_width / col_count)
    img_height = math.ceil(img_width / page_aspect_ratio)
    full_width = img_width * col_count
    full_height = img_height * row_count
    for i, commit in enumerate(commits):
        pdf_path = os.path.join(pdf_dir, f'{i}-{commit}.pdf')
        if not os.path.exists(pdf_path):
            continue
        img_path = os.path.join(img_dir, f'{i:05d}.png')
        if os.path.exists(img_path):
            print(f'Image for commit {i + 1}/{len(commits)} already exists. Skipping.')
            continue
        print(f'Creating image for commit {i + 1}/{len(commits)} ({commit}).')
        images = convert_from_path(pdf_path)
        image = Image.new('RGB', (full_width, full_height))
        image.paste((255, 255, 255), [0, 0, full_width, full_height])
        for j in range(len(images)):
            x = (j % col_count) * img_width
            y = (math.floor(j / col_count)) * img_height
            r_img = images[j].resize((img_width, img_height), resample=Image.BICUBIC)
            image.paste(r_img, (x, y))
        image.save(img_path)

    # create the final video
    ffmpeg.input(os.path.join(img_dir, '%05d.png'), pattern_type='sequence', start_number='00000', framerate=framerate).output(os.path.join(working_dir, 'latex-viz.mkv')).run()



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to the target git repository")
    parser.add_argument("--framerate", type=int, default=10, help="Framerate of the final video (default: 10)")
    parser.add_argument("--width", type=int, default=1920, help="Target width of the final video in pixels (default: 1920)")
    parser.add_argument("--aspect_ratio", type=float, default=16.0/9.0, help="Target aspect ratio of the final video (default: 16:9)")
    args = parser.parse_args()
    main(args.path, args.framerate, args.width, args.aspect_ratio)