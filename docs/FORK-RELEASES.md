# Fork release signing

This fork (`VoidInTheShell/u30air-openwrt`) uses its own release-signing key, not the upstream project's private
key. The public key is `rootfs/overlay/opt/mu300/lib/release.pub`; its usign key number is
`d95e780153427627`. The private key is kept outside the repository and supplied to GitHub Actions only through
`MU300_RELEASE_KEY`. Never commit it, include it in an artifact, or print it in a log.

## First signed release: v2026.10.28.1

The original build-only run [40701787821](https://github.com/VoidInTheShell/u30air-openwrt/actions/runs/40701787821)
built commit `46ae0efbe6561242e435fcf2c034eb924cb6b655`. Its firmware artifact was not signed and its root filesystems
still included the upstream public key. That artifact is not a signed release and should not be installed as one.

For the first fork release, reuse those already-built kernels, modules and extras **byte for byte**. On the local
maintainer machine only, rewrite each root filesystem archive to include the fork public key and the release's
updater, regenerate its embedded and companion image manifests with `tools/image-manifest.py`, and check that all
other archive contents and metadata are unchanged (including symlinks, hard links, ownership and PAX extended
attributes). Do not extract the archives onto a case-insensitive filesystem. Regenerate `SHA256SUMS`, then sign it
with `tools/sign-release.sh SHA256SUMS rootfs/overlay/opt/mu300/lib/release.pub` and verify it with both
`tools/usign-verify.py` and an independent signify/usign implementation. Publish provenance describing the original
run/commit and local repack. No kernel or module is recompiled by this procedure.

The public-key commit is the release tag's target. Publish as a prerelease, verify the uploaded files, and perform
the device smoke test from [RELEASING.md](RELEASING.md) before promotion. Do not claim that the repacked rootfs
archives are byte-identical to the original Actions artifacts. The unsigned original artifact remains untouched.

## Later releases and trust bootstrap

Future builds must include this public key from the outset and have the matching `MU300_RELEASE_KEY` secret.
Use the [normal release workflow](BUILD.md) with publishing explicitly enabled; preserve
signature verification and the prerelease/device-test gate. The existing release workflow is not changed by this
key setup.

A device with no previously pinned release key needs an authenticated first-key bootstrap: obtain the public key
from this repository/release over an authenticated connection, verify its fingerprint and the release signature
on the maintainer machine, and use the verified updater with that key pinned. Do not use `--unsigned`. A device
already pinned to another project key must not silently replace it; key rotation is a separate, explicit trust
change. Follow the supported `mu300-update` path, take private boot/NV/configuration backups first, retain both
rootfs and boot rollback, and verify the actual running release after reboot. Generic OpenWrt whole-disk
`sysupgrade` images are not suitable for this hardware.
