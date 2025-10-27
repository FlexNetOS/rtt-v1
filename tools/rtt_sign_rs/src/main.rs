use anyhow::*;
use base64::{engine::general_purpose, Engine as _};
use ed25519_dalek::{Signer, Verifier, SigningKey, VerifyingKey, Signature};
use std::{fs, path::PathBuf};

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    match args.get(1).map(String::as_str) {
        Some("gen") => {
            let sk = SigningKey::generate(&mut rand::rngs::OsRng);
            let vk: VerifyingKey = sk.verifying_key();
            println!("priv:{}", general_purpose::STANDARD.encode(sk.to_bytes()));
            println!("pub:{}", general_purpose::STANDARD.encode(vk.to_bytes()));
        }
        Some("sign") => {
            let key_b64 = args.get(2).context("need priv key b64")?;
            let file = PathBuf::from(args.get(3).context("need file")?);
            let bytes = fs::read(&file)?;
            let sk_bytes = general_purpose::STANDARD.decode(key_b64)?;
            let sk = SigningKey::from_bytes(sk_bytes[..32].try_into()?);
            let sig: Signature = sk.sign(&bytes);
            println!("{}", general_purpose::STANDARD.encode(sig.to_bytes()));
        }
        Some("verify") => {
            let pub_b64 = args.get(2).context("need pub key b64")?;
            let file = PathBuf::from(args.get(3).context("need file")?);
            let sig_b64 = args.get(4).context("need sig b64")?;
            let bytes = fs::read(&file)?;
            let vk_bytes = general_purpose::STANDARD.decode(pub_b64)?;
            let vk = VerifyingKey::from_bytes(&vk_bytes.try_into()? )?;
            let sig_bytes = general_purpose::STANDARD.decode(sig_b64)?;
            let sig = Signature::from_bytes(&sig_bytes.try_into()?);
            vk.verify(&bytes, &sig)?;
            println!("OK");
        }
        _ => eprintln!("usage: rtt-sign gen | sign <priv_b64> <file> | verify <pub_b64> <file> <sig_b64>"),
    }
    Ok(())
}
