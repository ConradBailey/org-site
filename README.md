# Org-Site #
## About ##
This is a static website generator built with blogs in mind. Org-Site
ingests [Org Mode](https://orgmode.org/) *source files*
and [Mustache](http://mustache.github.io/) *templates*, tracked with
`git`, and produces well-formatted, consistent, and organized HTML
pages.

## How to Use ##
* Invocation `$ ./org-site.py SRC DEST`
* `SRC` is the top level directory for your source files. It must be
  tracked by `git` for the retrieval of file metadata
  * *Important Note*: Only files /committed/ to the `git` repo will be
    recognized by the `org-site` rendering process.
* `DEST` is the directory where rendered folders and HTML files should
  be produced.


## Source File Layout ##
* `org-site` generally mirrors the organization of the destination
  directory according to the organization of the source directory.

* An `org-site` website is made up of *blogs*, and blogs are made up
  of *indexes* and *posts*.

* *Templates* are Mustache files with which `org-site` renders the
  posts and indexes into *HTML* files. *Indexes* and *posts* are Org
  files that provide content and values for the variables referenced
  by their corresponding *templates*

### Top Level Directory (Root) ###
This directory is the root of your source file tree and will be
referenced throughout this documentation as root and `/`, but it can
be anywhere in your filesystem. Your `.git` folder should be
here. Root should contain at a minimum
* An `index.org` that generates your home page.
* A `defaults.org`for assigning default values to template
  variables. These values will be inherited globally, but they can be
  overwritten by other Org files locally.
* A `templates` directory to contain all Mustache templates.
* Any other `.org` files in this directory will be treated like
  *posts* that do not belong to any blog. They will generate
  `index.html` files and links to them will be added to the navigation
  section.
  * Example: a file at `/about_me.org` containing ```#+NAV-NAME:
	About``` will generate `/about_me/index.html` according to the
	`post` template, and a corresponding link styled as `About` will
	be added to the navigation bar.

### Blog Directories ###
* Any directory under root that contains an `index.org` file is
  considered a *blog*. That `index.org` must contain whatever variable
  values and content is necessary for the `blog-index` template to
  process.
  * Example: `/turtle-grooming/index.org` containing `#+NAV-NAME:
	Turtles` will generate `/turtle-grooming/index.html` according to
	the `blog-index` template and `/turtle-grooming/rss.xml` will be
	generated according to the `rss` template. A link to the
	`index.html`, styled as `Turtles`, will be available in the `nav`
	template.

### Template Directory ###
* There must be a folder named `templates` directly under root. This
  will contain all `.mustache` templates necessary for site rendering
* There are a few *required* `.mustache` templates
  - `container` :: The outermost template which recursively holds all
    others. Usually `<!DOCTYPE html>` and `<html>...</html>` are
    here. No other template may depend on this one; otherwise circular
    dependencies are guaranteed.
  - `header` and `footer` :: For the HTML `<header>` and `<footer>`
    tags on every page.
  - `nav` :: For the navigation bar shared by every page
  - `blog-index` :: For generating the table of posts belonging to a
    blog.
  - `rss` :: For generating an `rss.xml` for a blog
  - `post` :: for the format of a post in a blog
