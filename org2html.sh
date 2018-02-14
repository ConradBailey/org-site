#!/bin/sh
":"; exec emacs --quick --script "$0" "$@" # -*-emacs-lisp-*-

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
