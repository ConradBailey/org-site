#!/bin/sh
":"; exec emacs --quick --script "$0" "$@" # -*-emacs-lisp-*-

(require 'org);

;; Add an embedded youtube link to org-mode (http://endlessparentheses.com/embedding-youtube-videos-with-org-mode-links.html)
(defvar yt-iframe-format
  ;; You may want to change your width and height.
  (concat "<iframe width=\"440\""
          " height=\"335\""
          " src=\"https://www.youtube.com/embed/%s\""
          " frameborder=\"0\""
          " allowfullscreen>%s</iframe>"))

(org-add-link-type
 "yt"
 (lambda (handle)
   (browse-url
    (concat "https://www.youtube.com/embed/"
            handle)))
 (lambda (path desc backend)
   (cl-case backend
     (html (format yt-iframe-format
                   path (or desc "")))
     (latex (format "\href{%s}{%s}"
                    path (or desc "video"))))))


(setq input-filename (pop argv))
(when argv
	(princ "org2html: Too many parameters provided")
	(terpri)
	(kill-emacs 1))

(unless input-filename
	(princ "org2html: Missing input filename")
	(terpri)
	(kill-emacs 1))

(if (file-readable-p input-filename)
		(progn (find-file input-filename)
					 (princ (org-export-as 'html nil nil t nil)))
	(princ (format "Error concerning input file: '%s'" input-filename))
	(terpri)
	(kill-emacs 1))

(kill-emacs 0)
