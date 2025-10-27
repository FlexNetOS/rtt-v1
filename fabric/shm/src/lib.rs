use anyhow::*;
use memmap2::{MmapMut};
use std::sync::atomic::{AtomicU32, Ordering::*};

#[repr(C)]
pub struct RingHeader {
    pub magic: u32,
    pub mask: u32,
    pub write: AtomicU32,
    pub read: AtomicU32,
}

pub struct SpscRing {
    mmap: MmapMut,
    hdr_off: usize,
    data_off: usize,
    slot_len: usize,
}

impl SpscRing {
    pub fn open(_path: &str, _slots: usize, _slot_len: usize) -> Result<Self> {
        // TODO: create shared mem, map both ends; placeholder uses file-backed mmap
        let len = 1<<20;
        let file = tempfile::tempfile()?;
        let mmap = unsafe { MmapMut::map_mut(&file)? };
        Ok(Self{ mmap, hdr_off:0, data_off:64, slot_len:_slot_len })
    }
    pub fn push(&mut self, _frame: &[u8]) -> Result<()> { Ok(()) }
    pub fn pop(&mut self) -> Result<Option<Vec<u8>>> { Ok(None) }
}
