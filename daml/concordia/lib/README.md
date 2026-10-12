# Concordia data dependencies

From a fresh SyncVotes checkout, run `python3 scripts/build-concordia-deps.py` before
`dpm build --all`. This downloads the pinned Concordia source archive over HTTPS,
verifies its SHA-256, builds only the six required Daml packages with `dpm` SDK
3.4.11 in a disposable temporary directory, and installs their DARs together with
the two verified upstream binaries in this directory. It does not read `../concordia`.
Set `DPM` to the absolute path of another dpm installation if necessary. SyncVotes
itself builds with SDK 3.5.7; all these packages target Daml LF 2.1.

Source: https://github.com/unlockitio/concordia/tree/ac516498da433f1e6b211f5b7c6cc9c9ba2ec549
Archive: https://codeload.github.com/unlockitio/concordia/tar.gz/ac516498da433f1e6b211f5b7c6cc9c9ba2ec549
Archive SHA-256: `6b135273c4f746511a9d2b92d46722b550fb0a23a1fcc84d6bb3ca42d2d0cb0e`

The six `cap-*` binaries are generated from Concordia's Apache-2.0 sources.
The two `splice-*` DARs are exact tracked blobs in that same Concordia revision
(introduced there in commit `1ba8960ea3eaea9b075825f44eeb2e72dd23f1a9`).
Their embedded DAR manifests identify `splice-api-token-metadata-v1-1.0.0`
(SDK 3.3.0 snapshot, package ID `4ded6b668cb3b64f7a88a30874cd41c75829f5e064b3fbbadf41ec7e8363354f`)
and `splice-util-0.1.7` (SDK 3.5.2, package ID
`b5be6316177384677c024316c0bfaf7d3d494e7c3ad6c540d2032e6112b004bc`).
Concordia's Apache license does not by itself establish rights to redistribute
third-party Splice binaries. All eight DARs therefore remain ignored, local build
inputs, not committed to SyncVotes. `SHA256SUMS` pins their exact contents;
`(cd daml/concordia/lib && shasum -a 256 -c SHA256SUMS)` checks a generated set.
The script verifies the archive and Splice bytes before compilation, checks all
eight DARs against `SHA256SUMS` before installing them, and prints their hashes;
generated hashes were reproduced in separate clean temporary builds with the
installed SDK. Any dependency update requires
reviewing its source and refreshing the archive and DAR hashes deliberately.
