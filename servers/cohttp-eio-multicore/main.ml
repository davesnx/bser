let body = "Hello, World!"

let headers =
  Cohttp.Header.of_list
    [ ("content-type", "text/plain"); ("content-length", "13") ]

let callback _conn _request _request_body =
  Cohttp_eio.Server.respond_string ~headers ~status:`OK ~body ()

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
  Eio_main.run @@ fun env ->
  Eio.Switch.run @@ fun sw ->
  let socket =
    Eio.Net.listen ~sw ~reuse_addr:true ~backlog:1024 (Eio.Stdenv.net env)
      (`Tcp (Eio.Net.Ipaddr.V4.any, port))
  in
  let server = Cohttp_eio.Server.make ~callback () in
  Cohttp_eio.Server.run
    ~additional_domains:(Eio.Stdenv.domain_mgr env, total_domains - 1)
    ~on_error:raise socket server
