package main
import (
  "bufio"
  "encoding/json"
  "fmt"
  "os"
)
type Req struct { Id string `json:"id"`; Method string `json:"method"`; Params any `json:"params"` }
func main(){
  in := bufio.NewScanner(os.Stdin)
  for in.Scan() {
    var r Req
    if err := json.Unmarshal([]byte(in.Text()), &r); err != nil { continue }
    out := map[string]any{ "id": r.Id, "result": map[string]bool{"ok": true}, "error": nil }
    b,_ := json.Marshal(out); fmt.Println(string(b))
  }
}
