# ViewFS (starter)
This starter materializes provider views into real files. For elite mode, replace with a FUSE/WinFsp daemon that presents virtual files from CAS + overlays at read-time.
Fallback order: VFS → hardlink → symlink → proxy JSON.
