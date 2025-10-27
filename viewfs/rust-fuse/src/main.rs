use anyhow::*;
use fuse3::{raw::Filesystem, MountOptions, Session};
use std::{path::PathBuf, sync::Arc};
use tokio::runtime::Runtime;

#[derive(Clone)]
struct ViewFs {
    cas_dir: PathBuf,
    overlays_dir: PathBuf,
    index_file: PathBuf,
}

#[fuse3::async_trait]
impl Filesystem for ViewFs {}

fn main() -> Result<()> {
    let cas = PathBuf::from(".rtt/registry/cas/sha256");
    let overlays = PathBuf::from("overlays");
    let index = PathBuf::from(".rtt/registry/index.json");
    let mount = std::env::args().nth(1).expect("mount path required");
    let rt = Runtime::new()?;
    let fs = ViewFs { cas_dir: cas, overlays_dir: overlays, index_file: index };
    rt.block_on(async move {
        let session = Session::new(Arc::new(fs), MountOptions::default().fs_name("rtt-viewfs")).await?;
        session.mount(mount).await?;
        session.await;
        Ok::<_, anyhow::Error>(())
    })?;
    Ok(())
}
