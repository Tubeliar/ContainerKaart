# ContainerKaart

This is a small project to keep track of waste bins (afval containers) in a small community.
Default settings will all be hardcoded because of the single use nature of this repo, but they should be easy to adjust if you want to reuse it.

## Building

`site/index.html` is generated from `site/index.template.html` by inlining the SVG icon files as a symbol sprite. This is necessary because browsers handle cross-document `<use href="file.svg#id">` references inconsistently — Chrome supports them, but Firefox blocks them and VSCode's SVG preview ignores them entirely. Inlining all symbols into the HTML itself avoids that problem without duplicating shared parts like gradients.

After editing `index.template.html` or any of the `site/*.svg` files, regenerate `index.html` with:

```bash
python tools/inline_svg.py
```

The SVG files in `site/` (`container-icon.svg`, `container-with-litter.svg`, etc.) are the source of truth for the icons and should be edited directly. Do not edit the generated `index.html` by hand.

## Running

Install dependencies and start the server:

```bash
pip install -r requirements.txt
python server.py
```

Then visit http://127.0.0.1:8080 in your browser.
