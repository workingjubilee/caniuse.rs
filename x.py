#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys


def main():
    if len(sys.argv) < 2:
        print(
            """
            usage: ./x.py <command> [options...] [-- <extra_options>...]
                commands: build, deploy
                options:
                    --dev        Create a development build. Passed to wasm-pack.
                    --profiling  Create a profiling build. Passed to wasm-pack.
                    --release    Create a release build. Passed to wasm-pack.
                extra options will be passed to cargo build
            """
        )
        sys.exit(1)

    command = sys.argv[1]

    if command == "build":
        build()
    elif command == "deploy":
        deploy()


def run(*args):
    subprocess.run(args).check_returncode()


def build():
    run("wasm-pack", "build", "--no-typescript", "--target", "web", *sys.argv[2:])
    shutil.copyfile("pkg/caniuse_rs_bg.wasm", "public/caniuse_rs.wasm")
    run(
        "rollup", "src/main.js", "--format", "iife", "--file", "public/caniuse_rs.js",
    )
    # TODO: shutil.copytree()?
    static_files = map(lambda file: f"static/{file}", os.listdir("static"))
    run(
        "cp", "-r", *static_files, "public/",
    )


def deploy():
    build()
    run("rsync", "-rzz", "public", "caniuse.rs:/tmp/caniuse/")
    run(
        "ssh",
        "caniuse.rs",
        """
        set -e
        sudo chown root: /tmp/caniuse/public
        sudo rsync -r --delete /tmp/caniuse/public/* /srv/http/caniuse.rs/
        sudo rm -r /tmp/caniuse/public
        """,
    )


if __name__ == "__main__":
    main()
