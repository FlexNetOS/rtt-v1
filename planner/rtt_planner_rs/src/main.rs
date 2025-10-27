use anyhow::*;
use serde::{Deserialize, Serialize};
use sha2::{Sha256, Digest};
use std::{fs, path::PathBuf};

#[derive(Serialize, Deserialize, Clone)]
struct Route { from:String, to:String }
#[derive(Serialize, Deserialize)]
struct Routes { routes: Vec<Route> }

#[derive(Serialize, Deserialize)]
struct Plan {
    plan_id: String,
    routes_add: Vec<Route>,
    routes_del: Vec<Route>,
    order: Vec<String>,
    sign: Option<Sign>,
}
#[derive(Serialize, Deserialize)]
struct Sign { alg:String, key_id:String, sig:String }

fn hash_bytes(b: &[u8]) -> String {
    let mut h = Sha256::new(); h.update(b); format!("sha256-{:x}", h.finalize())
}

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 4 { bail!("usage: rtt-planner <routes.json> <manifests_dir> <out_plan.json> [sign_key_b64]"); }
    let routes: Routes = serde_json::from_str(&fs::read_to_string(&args[1])?)?;
    let _mani_dir = PathBuf::from(&args[2]);
    let mut plan = Plan {
        plan_id: "sha256-PLACEHOLDER".to_string(),
        routes_add: routes.routes.clone(),
        routes_del: vec![],
        order: vec!["BATCH-1".into()],
        sign: None,
    };
    let plan_json = serde_json::to_vec(&plan)?;
    let pid = hash_bytes(&plan_json);
    plan.plan_id = pid.clone();
    let out = PathBuf::from(&args[3]);
    fs::write(&out, serde_json::to_vec_pretty(&plan)?)?;
    if args.len() > 4 {
        let sig = std::process::Command::new("./tools/rtt_sign_rs/target/release/rtt-sign")
            .args(["sign", &args[4], &out.to_string_lossy() ]).output();
        if let Ok(o) = sig {
            if o.status.success() {
                let s = String::from_utf8_lossy(&o.stdout).trim().to_string();
                let mut plan2 = plan; plan2.sign = Some(Sign{alg:"ed25519".into(), key_id:"dev".into(), sig:s});
                fs::write(&out, serde_json::to_vec_pretty(&plan2)?)?;
            }
        }
    }
    println!("{}", pid);
    Ok(())
}
