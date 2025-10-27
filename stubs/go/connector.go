// go: connector stub
package main
import("bufio";"os";"fmt")
func main(){ in:=bufio.NewScanner(os.Stdin); if in.Scan(){ fmt.Println("{\"id\":\"0\",\"result\":{\"ok\":true},\"error\":null}") } }
