# Code Signing Policy

Free code signing provided by SignPath.io, certificate by SignPath Foundation.

## Scope

This policy covers the official `IOSoccer Troubleshooter.exe` release asset built from this repository. IOSoccer, Steam, game files, user configuration, and third-party software are outside the signing scope.

Current releases remain unsigned until SignPath Foundation accepts the project. Signed releases will be identified in their release notes and verifiable with Windows Authenticode.

## Build and approval process

1. Release source is committed to the default branch and tagged.
2. GitHub Actions compiles the Python source, installs pinned project requirements, and creates the executable on a clean Windows runner.
3. The designated approver reviews the source revision and signing request.
4. SignPath signs only the approved executable with its HSM-protected key.
5. The signature is verified before the checksum and GitHub release asset are published.

## Project roles

- Committer and reviewer: [SyroxXploits](https://github.com/SyroxXploits)
- Signing approver: [SyroxXploits](https://github.com/SyroxXploits)

Third-party contributions require maintainer review before merge. Repository and signing accounts must use multi-factor authentication.

See the [privacy policy](PRIVACY.md) and [security policy](SECURITY.md).
