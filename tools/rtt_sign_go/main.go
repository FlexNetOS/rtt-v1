package main
import (
    "crypto/ed25519"
    "crypto/rand"
    "encoding/base64"
    "fmt"
    "io/ioutil"
    "os"
)
func main(){
    if len(os.Args) < 2 { fmt.Println("usage: gen | sign <priv_b64> <file> | verify <pub_b64> <file> <sig_b64>"); return }
    switch os.Args[1] {
    case "gen":
        pub, priv, _ := ed25519.GenerateKey(rand.Reader)
        fmt.Println("priv:"+base64.StdEncoding.EncodeToString(priv))
        fmt.Println("pub:"+base64.StdEncoding.EncodeToString(pub))
    case "sign":
        priv_b64 := os.Args[2]; file := os.Args[3]
        priv, _ := base64.StdEncoding.DecodeString(priv_b64)
        msg, _ := ioutil.ReadFile(file)
        sig := ed25519.Sign(ed25519.PrivateKey(priv), msg)
        fmt.Println(base64.StdEncoding.EncodeToString(sig))
    case "verify":
        pub_b64 := os.Args[2]; file := os.Args[3]; sig_b64 := os.Args[4]
        pub, _ := base64.StdEncoding.DecodeString(pub_b64)
        msg, _ := ioutil.ReadFile(file)
        sig, _ := base64.StdEncoding.DecodeString(sig_b64)
        if ed25519.Verify(ed25519.PublicKey(pub), msg, sig) { fmt.Println("OK") } else { fmt.Println("FAIL") }
    }
}
