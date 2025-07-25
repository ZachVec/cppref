# cppref

A cli pragram for cpp programmers to lookup cppreference!

> [!Info]
> This project is under development, pull requests are welcomed.

## Expected Features

- Syntax highlight support
- Easy to integrate with fzf
- Shipped with neovim plugin which can be integrated with fzf-lua.nvim
- Cache pages on the fly or cache pages once and for all.
- Import / export data files so that offline machines are able to access

## Q&A

- Q: Why not `cppman`?
- A: cppman use regex to format document, whereas this project format document
by parsing html using xpath.

## Bugs

Please report bugs under the github issues section.

## TODO

- [ ] parse html correctly
  - [x] `<p>`: text
  - [x] `<div>`: text
  - [x] `<h3>`: section header
  - [x] `<ol>` ordered list
  - [x] `<ul>` unordered list
  - [ ] `<table>` table
  - [ ] more tags ...
- [ ] Visit pages Syncly.
- [ ] Cache pages Asyncly.
