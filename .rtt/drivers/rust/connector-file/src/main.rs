use anyhow::*;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::io::{self, Read, Write};

#[derive(Deserialize)]
struct Req { id:String, method:String, params:Option<Value> }

fn main()->Result<()>{
    let mut buf = String::new();
    io::stdin().read_to_string(&mut buf)?;
    for line in buf.lines(){
        if line.trim().is_empty(){ continue; }
        let req: Req = serde_json::from_str(line)?;
        let res = json!({"id": req.id, "result": {"ok": true}, "error": null});
        writeln!(io::stdout(), "{}", serde_json::to_string(&res)?)?;
    }
    Ok(())
}
