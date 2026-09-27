# clyon.dev

My blog, served by GitHub Pages from this repo. `loose-ends/` is Loose Ends' own site and is left alone.

## Post something

```sh
python3 build.py new blogs "Title of the post"   # or: new life "Title"
```

That creates `posts/blogs/YYYY-MM-DD-title-of-the-post.md`. Write it in Markdown, then commit and push. A GitHub Action rebuilds the site; it's live a minute or two later.

The header between the `---` lines:

| field  | used for                                              |
|--------|-------------------------------------------------------|
| title  | the post title (optional for life posts)              |
| dek    | one-line summary under the title (blogs)              |
| kind   | Update, Note or Photo (life)                          |
| photo  | `images/name.jpg` shown above a life post             |
| draft  | `true` keeps it off the site (but the repo is public) |

Images go in `posts/blogs/images/` or `posts/life/images/`, referenced as `images/name.jpg`.

## Preview locally

```sh
python3 build.py && python3 -m http.server 8790
```

Then open http://localhost:8790. Everything outside `posts/`, `assets/`, `build.py`, `favicon.svg`, `loose-ends/` and `CNAME` is generated.
