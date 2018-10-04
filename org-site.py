#! /usr/bin/env python3

import pystache
import sys
import re
import subprocess
import os
import urllib.parse
import datetime
import dateutil.tz
import datetime
import shutil
import argparse
from collections import defaultdict as ddict


prog_name = os.path.basename(sys.argv[0])


def err(x):
  print("{}: Error - {}".format(prog_name, x), file=sys.stderr)
  sys.exit(1)


def log(x):
  print(x, file=sys.stderr)


def build_arg_parser():
  parser = argparse.ArgumentParser(description = "Publish org files in SRC as html in DEST",
                                   epilog = "Report bugs to: conrad@cbailey.tech\norg-site home page: <https://github.com/ConradBailey/org-site>",
                                   formatter_class = argparse.RawTextHelpFormatter)
  parser.add_argument("SRC", help="directory containing hierarchy of org files")
  parser.add_argument("DEST", help="directory where html files exported from SRC will be saved")
  return parser

default_vars = {}


def get_context(org_file):
  org_content = open(org_file, 'r').read()
  results = re.findall(r'\#\+(.*?):\s*(.*)\s*', org_content)
  context = dict()
  for name, value in results:
    if name[-4:] == "LIST":
      value = [{name[:-5].lower(): x} for x in value.split()]
    elif value.lower() == 'none':
      value = None
    elif value.lower() == 'false':
      value = False
    context[name.lower()] = value
  return context


def sitemap_url_block(url, lastmod, changefreq):
  return '''\
  <url>
    <loc>{}</loc>
    <lastmod>{}</lastmod>
    <changefreq>{}</changefreq>
  </url>
'''.format(url, lastmod, changefreq)


def str2url(s):
  return urllib.parse.quote(s.lower().replace(' ','_'))


def org2html(org_path):
  content = subprocess.run("org2html.sh {}".format(org_path).split(), stdout=subprocess.PIPE, universal_newlines=True).stdout
  if (len(content.strip()) == 0):
    content = None
  return content


def render_page(content, context):
  context = context.copy()
  context['content'] = content
  templates_dir = context['templates-dir']
  for part in ['header', 'footer', 'container']:
    part_path = os.path.join(templates_dir, context['{}-template'.format(part)])
    part_src = open(part_path, 'r').read()
    context[part] = pystache.render(part_src, context)
  return context['container']

class Org_Site:
  def __init__(self, src_path, dst_path):
    self.required_dirs = ['templates']
    self.required_templates = ['header', 'post', 'footer', 'nav', 'container', 'blog-index', 'rss']

    self.src_path = src_path
    self.dst_path = dst_path

    self.context = self._generate_default_context()
    self._sanity_check()

    self.top_blog = Blog(self.src_path)
    self.blogs = self._get_blogs()

    self.context['nav'] = self._build_nav()

  def render(self):
    for blog in self.blogs:
      blog.render(self.dst_path, self.context)
    for post in self.top_blog.posts:
      post.render(self.dst_path, self.context)

    context = self.context.copy()
    index_path = os.path.join(self.src_path, 'index.org') #should be self.index_path when inheriting from blog!
    self.index_post = Post(index_path)
    self.index_post.render(self.dst_path, context)

    self.build_sitemap(context)
    self.build_robotstxt(context)

  def build_sitemap(self, context):
    sitemap = open(os.path.join(self.dst_path, 'sitemap.xml'), 'w')
    sitemap.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    sitemap.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')

    site_url = context['site-url']
    sitemap.write(sitemap_url_block(site_url, self.index_post.context['last-mod'], 'weekly'))
    for blog in self.blogs:
      blog_url = os.path.join(site_url, blog.context['nav-url'])
      sitemap.write(sitemap_url_block(blog_url, min([x.context['last-mod'] for x in blog.posts]), 'weekly'))
      for post in blog.posts:
        post_url = os.path.join(blog_url, post.context['nav-url'])
        sitemap.write(sitemap_url_block(post_url, post.context['last-mod'], 'weekly'))
    for post in self.top_blog.posts:
      post_url = os.path.join(blog_url, post.context['nav-url'])
      sitemap.write(sitemap_url_block(post_url, post.context['last-mod'], 'weekly'))

    sitemap.write('</urlset>\n')
    sitemap.close()

  def build_robotstxt(self, context):
    robotstxt = open(os.path.join(self.dst_path, 'robots.txt'), 'w')
    sitemap_path = os.path.join(context['site-url'], 'sitemap.xml')
    robotstxt.write("Sitemap: {}\n".format(sitemap_path))
    robotstxt.close()

  def _generate_default_context(self):
    # Default to None
    context = ddict(lambda: None)

    # Required Directory Locations
    for dir_name in self.required_dirs:
      context['{}-dir'.format(dir_name)] = os.path.join(self.src_path, dir_name)

    # Required Template Locations
    for template_name in self.required_templates:
      context['{}-template'.format(template_name)] = '{}.mustache'.format(template_name)

    # Default Non-None Contexts
    context['language'] = 'en-us'
    context['show-nav-links'] = True
    context['show-meta'] = True

    # Overwrite with user designated values
    default_org_path = os.path.join(self.src_path, 'defaults.org')
    try:
      context.update(get_context(default_org_path))
    except:
      err("extracting context from {}".format(default_org_path))

    return context


  def _sanity_check(self):
    # Check existences
    if not os.path.isdir(self.dst_path):
      err("{} is not a directory".format(self.dst_path))
    if not os.path.isdir(self.src_path):
      err("{} is not a directory".format(self.src_path))
    if not os.path.isfile(os.path.join(self.src_path, 'index.org')):
      err("index.org missing from {}".format(self.src_path))
    if not os.path.isfile(os.path.join(self.src_path, 'defaults.org')):
      err("defaults.org missing from {}".format(self.src_path))

    for dir_path in self.required_dirs:
      var_name = '{}-dir'.format(dir_path)
      if not os.path.isdir(os.path.join(self.src_path, self.context[var_name])):
        err("{} value '{}' is not a directory".format(var_name, self.context[var_name]))
    for template_name in self.required_templates:
      var_name = '{}-template'.format(template_name)
      file_path = os.path.join(self.src_path, self.context['templates-dir'], self.context[var_name])
      if not os.path.isfile(file_path):
        err("{} value '{}' is not a file".format(var_name, self.context[var_name]))



  # Categorize top-level files into posts, blogs, and others.
  def _get_blogs(self):
    blogs = []
    top_level_paths = subprocess.run("git ls-tree --name-only master .".split(), cwd=self.src_path, stdout=subprocess.PIPE, universal_newlines=True).stdout.split('\n')[:-1]
    top_level_paths = [os.path.join(self.src_path, x) for x in top_level_paths]
    for file_path in top_level_paths:
      base, ext = os.path.splitext(os.path.basename(file_path))
      if base == self.context['templates-dir']:
        continue
      if os.path.isdir(file_path) and os.path.isfile(os.path.join(file_path, 'index.org')):
        blogs.append(Blog(file_path))

    return blogs

  def _build_nav(self):
    nav_links = []
    for x in (self.blogs + self.top_blog.posts):
      nav_links.append({'nav-name': x.context['nav-name'],
                        'nav-url' : x.context['nav-url']})

    # Build the navigation section
    self.context.update({'nav-links': nav_links})
    nav_template = open(os.path.join(self.src_path, self.context['templates-dir'], self.context['nav-template']), 'r').read()
    return pystache.render(nav_template, self.context)



class Blog:
  def __init__(self, src_path=None):
    self.src_path = src_path
    self.index_path = os.path.join(self.src_path, 'index.org')
    self.posts, self.copyq = self._categorize_contents()
    self.context = self._generate_default_context()

  def _generate_default_context(self):
    context = ddict(lambda: None)

    # Provide reasonable defaults
    if not context['nav-name']:
      context['nav-name'] = context['title']
    context['nav-url'] = str2url(os.path.basename(self.src_path))
    context['blog-url'] = context['nav-url']
    context['rss-url'] = 'rss.xml'

    # Build posts context for indexing
    context['posts'] = [post.context for post in self.posts]

    # Gather description from index org page
    context['content'] = org2html(self.index_path)

    # Override defaults with user preferences
    context.update(get_context(self.index_path))
    return context


  def _categorize_contents(self):
    posts = []
    copyq = []
    contents = subprocess.run("git ls-tree --name-only master .".split(), cwd=self.src_path, stdout=subprocess.PIPE, universal_newlines=True).stdout.split('\n')[:-1]
    contents = [os.path.join(self.src_path, x) for x in contents]
    for file_path in contents:
      basename = os.path.basename(file_path)
      base, ext = os.path.splitext(basename)
      if basename in ['defaults.org', 'index.org']:
        continue
      elif os.path.isfile(file_path) and ext == '.org':
        posts.append(Post(file_path))
      else:
        copyq.append(file_path)
    return posts, copyq


  # Create the blog dir, write index.html and rss.xml, and render posts
  def render(self, dst_path, context):
    context = context.copy()
    context.update(self.context)

    # Create destination directory for renderings
    blog_dir = os.path.join(dst_path, self.context['nav-url'])
    if not os.path.isdir(blog_dir):
      os.makedirs(blog_dir)

    blog_index = self._render_blog_index(context)
    open(os.path.join(blog_dir, 'index.html'), 'w').write(blog_index)

    rss = self._render_rss(context)
    open(os.path.join(blog_dir, 'rss.xml'), 'w').write(rss)

    for post in self.posts:
      post.render(blog_dir, context)
    #for copy in self.copyq:
    #  log(copy)

  def _render_blog_index(self, context):
    template_path = os.path.join(context['templates-dir'], context['blog-index-template'])
    template = open(template_path, 'r').read()
    context['posts'] = sorted(context['posts'], key=lambda x: x['exact-creation'], reverse=True)
    #context['content'] = org2html(self.src_path)
    content = pystache.render(template, context)
    return render_page(content, context)

  def _render_rss(self, context):
    localtz = dateutil.tz.tzlocal()
    context['current-time'] = datetime.datetime.now(localtz).strftime('%a, %d %b %Y %H:%M:%S %Z')
    template_path = os.path.join(context['templates-dir'], context['rss-template'])
    template = open(template_path, 'r').read()
    return pystache.render(template, context)


class Post:
  def __init__(self, src_path=None):
    self.src_path = src_path
    self.context = self._generate_default_context()

  def _generate_default_context(self):
    context = ddict(lambda: None)

    # Provide reasonable defaults
    base, ext = os.path.splitext(os.path.basename(self.src_path))
    if not context['nav-name']:
      context['nav-name'] = base

    context['nav-url'] = str2url(context['nav-name'])

    context.update(self._get_dates())

    context.update(get_context(self.src_path))
    return context

  def _get_dates(self):
    git_dir, basename = os.path.split(self.src_path)
    mods = subprocess.run("git log --format=%aD {}".format(basename).split(), cwd=git_dir, stdout=subprocess.PIPE, universal_newlines=True).stdout.split('\n')[:-1]
    mods = [datetime.datetime.strptime(x, '%a, %d %b %Y %H:%M:%S %z') for x in mods]
    return {'exact-creation' : mods[-1].strftime('%Y-%m-%d %H:%M:%S:%f'),
            'creation' : mods[-1].strftime('%Y-%m-%d'),
            'last-mod' : mods[0].strftime('%Y-%m-%d')}

  def render(self, dst_path, context):
    context = context.copy()
    context.update(self.context)
    if ('index' != self.context['nav-url']):
      post_dir = os.path.join(dst_path, self.context['nav-url'])
    else:
      post_dir = dst_path

    if not os.path.isdir(post_dir):
      os.makedirs(post_dir)

    template_path = os.path.join(context['templates-dir'], context['post-template'])
    template = open(template_path, 'r').read()
    context['content'] = org2html(self.src_path)
    content = pystache.render(template, context)
    render = render_page(content, context)
    open(os.path.join(post_dir, 'index.html'), 'w').write(render)

def main():
  parser = build_arg_parser()
  args = parser.parse_args()
  src_dir = args.SRC
  dst_dir = args.DEST

  site = Org_Site(src_dir, dst_dir)
  site.render()


if __name__ == "__main__":
  main()
