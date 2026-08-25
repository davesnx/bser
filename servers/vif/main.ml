let text = "Hello, World!"

let hello request _server () =
  let open Vif.Response.Syntax in
  let* () = Vif.Response.add ~field:"content-type" "text/plain" in
  let* () = Vif.Response.with_string request text in
  Vif.Response.respond `OK

let routes =
  let open Vif.Uri in
  let open Vif.Route in
  [ get (rel /?? nil) --> hello ]

let () =
  let port =
    match Sys.getenv_opt "PORT" with Some value -> int_of_string value | None -> 8080
  in
  let sockaddr = Unix.(ADDR_INET (inet_addr_any, port)) in
  let cfg = Vif.config ~domains:0 ~with_rng:false sockaddr in
  Miou_unix.run ~domains:0 @@ fun () -> Vif.run ~cfg routes ()
