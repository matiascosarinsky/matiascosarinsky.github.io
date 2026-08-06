# Matias Cosarinsky — academic website

This is a lightweight GitHub Pages site. It is plain HTML, CSS, and JavaScript, so it needs no build system.

## Publish it

1. Create a GitHub repository named `matiascosarinsky.github.io`.
2. Push the contents of this folder to the repository.
3. In **Settings → Pages**, choose **GitHub Actions** as the source.

The site will be available at `https://matiascosarinsky.github.io/`.

## Automatic publications

The workflow in `.github/workflows/update-publications.yml` runs on the first day of every month and can also be started manually from the **Actions** tab. It reads the Google Scholar profile with ID `j7pWCTgAAAAJ`, including the publication venue/journal when Scholar provides it, updates `data/publications.json`, and commits changes back to the repository.

The workflow can email you when new publications are found. To enable this, add repository secrets named `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, and `SMTP_PASSWORD` under **Settings → Secrets and variables → Actions**. For Gmail, use an App Password rather than your regular password. The email will list the new papers and point you to `assets/publication-links.json` for optional links.

Google Scholar does not provide an official public API, so Scholar can occasionally rate-limit automated requests. If an update fails, the existing publication list remains unchanged; run the workflow manually later.

Paper links are filled automatically from Google Scholar. Add optional project page, code, dataset, and demo links in `assets/publication-links.json`; buttons only appear when their fields contain a URL. The buttons always appear in this order: Project Page, Paper, Code, Dataset, Demo.

When the updater sees a publication, it creates a folder for it under `assets/figures/`. Put one `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, or `.pdf` file in that folder; the first supported file will be displayed as a small Figure 1 thumbnail to the left of the publication. PDFs are converted to a generated `figure-1.png` thumbnail; the original PDF is never overwritten.

For local PDF conversion, install the correct package with `python -m pip install PyMuPDF`. The thumbnail is generated only when `figure-1.png` does not already exist.

The paper title itself links to the paper. For arXiv papers, the updater attempts to inspect the first two PDF pages for equal-contribution language and an asterisk/footnote marker next to an author. PDF extraction is imperfect, so a manual `equal_contributors` override remains available when needed.

## Personalize it

- Replace the `MC` placeholder in `index.html` with an image when you have a profile photo.
- Upload your CV as `assets/cv.pdf`.
- Edit the profile links in `index.html`.
- Add project/code/demo/dataset URLs to `data/publication-overrides.json`.
