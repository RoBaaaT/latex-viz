# latex-viz

Visualize the evolution of your LaTeX manuscript as a video.

## Summary

latex-viz is a small python script that takes a git repository containing a LaTeX manuscript and creates a short video showing the evolution of the manuscript.
This is done by compiling the manuscript at each commit below HEAD and creating an image preview of the resulting PDF.
The image previews are then concatenated into the final video.

## Using latex-viz

### Prerequisites

The following software needs to be installed to run latex-viz:
* `python3`
* `git`
* `ffmpeg`
* A LaTeX installation with the required packages to compile your manuscript and `latexmk`

Python packages:
* `pyPDF2` (to get PDF page counts)
* `pdf2image` (to convert PDFs to images)
* `ffmpeg-python` (ffmpeg python bindings to generate the final video)

### Running latex-viz

The simplest way to use latex-viz is to just run
```
python3 latex-viz.py <path to manuscript git repository>
```

This will execute the steps described above and finally produce the output video in the specified directory.
Depending on the number of commits in the repository, this may take a while.
The created PDFs and images will also be saved in the `latex-viz-pdfs` and `latex-viz-imgs` directories inside the specified directory.
This allows latex-viz to continue where it left off if it is interrupted for any reason.
In that case you can simply run the command again to continue the process.

There are also some optional arguments, e.g., to set the width in pixels and target aspect ratio of the final video (which affects the grid the PDF pages are arranged in).
These can be found by running:
```
python3 latex-viz.py --help
```