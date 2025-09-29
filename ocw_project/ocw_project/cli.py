import os
import panel as pn
import ocw_project.viewer.frontend_app as app

def main():
    in_docker = os.environ.get("IN_DOCKER", "0") == "1"

    pn.extension()
    pn.serve(
        {"frontend_app": app.dashboard},  # mounted at /frontend_app
        show=not in_docker,
        port=5006,
        autoreload=not in_docker,
        address="0.0.0.0" if in_docker else "localhost",
        allow_websocket_origin=["*"] if in_docker else None,
    )

if __name__ == "__main__":
    main()
