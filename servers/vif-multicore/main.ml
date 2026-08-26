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
  let total_domains =
    match Sys.getenv_opt "BSER_CPU_COUNT" with
    | Some value -> int_of_string value
    | None -> Domain.recommended_domain_count ()
  in
  if total_domains < 2 then invalid_arg "BSER_CPU_COUNT must be at least 2";
  let worker_domains = total_domains - 1 in
  let sockaddr = Unix.(ADDR_INET (inet_addr_any, port)) in
  let cfg = Vif.config ~domains:worker_domains ~with_rng:false sockaddr in
  Miou_unix.run ~domains:worker_domains @@ fun () -> Vif.run ~cfg routes ()
