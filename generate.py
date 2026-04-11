import os

PHOTOS_DIR = "photos"
GALLERY_FILE = "photos2.html"


def format_title(name):
    return name.replace("_", " ").title()


def create_photo_page(name, ext):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>BNS</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="/style.css">
</head>

<body>

<nav class="navbar">
  <a href="/index.html">About</a>
  <a href="/photos.html">Photos</a>
</nav>

<div class="container">

  <h1 class="page-title">{format_title(name)}</h1>

  <div class="feature-image">
    <img src="{name}{ext}" alt="{name}">
  </div>

  <div class="image-meta">
    <span class="location">TODO</span>
    <span class="date">TODO</span>
  </div>

  <div class="photo-details">
    <div class="notes">
      <p><strong>Notes:</strong></p>
      <p>TODO</p>
    </div>
  </div>

</div>

</body>
</html>
"""


def create_gallery_item(name, ext):
    return f"""
      <figure>
        <a href="photos/{name}.html">
          <img src="photos/{name}{ext}" alt="{format_title(name)} photo">
          <figcaption>{format_title(name)}</figcaption>
        </a>
      </figure>
"""


def main():
    files = os.listdir(PHOTOS_DIR)

    items = []

    for file in files:
        name, ext = os.path.splitext(file)

        if ext.lower() not in [".jpg", ".jpeg", ".png"]:
            continue

        html_path = os.path.join(PHOTOS_DIR, f"{name}.html")

        # Create page if it doesn't exist
        if not os.path.exists(html_path):
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(create_photo_page(name, ext))
            print(f"Created page: {name}.html")

        items.append((name, ext))

    # 🔥 Sort newest first
    items.sort(
        key=lambda x: os.path.getmtime(os.path.join(PHOTOS_DIR, x[0] + x[1])),
        reverse=True
    )

    gallery_items = "".join(create_gallery_item(name, ext) for name, ext in items)

    gallery_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>BNS</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="style.css">
</head>

<body>

<nav class="navbar">
  <a href="index.html">About</a>
  <a href="photos.html"><strong>Photos</strong></a>
</nav>

<div class="container">

  <h1 class="page-title">Photos</h1>

  <div class="gallery">
    {gallery_items}
  </div>

</div>

</body>
</html>
"""

    with open(GALLERY_FILE, "w", encoding="utf-8") as f:
        f.write(gallery_page)

    print("photos2.html fully rebuilt")


if __name__ == "__main__":
    main()