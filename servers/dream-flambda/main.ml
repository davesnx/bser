let port =
  match Sys.getenv_opt "PORT" with Some p -> int_of_string p | None -> 8080

let () =
  Dream.run ~interface:"0.0.0.0" ~port
  @@ Dream.router
       [
         Dream.get "/" (fun _request ->
             Dream.respond
               ~headers:[ ("Content-Type", "text/plain") ]
               "Hello, World!");
       ]
