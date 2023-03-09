# GitHub Actions for the Ñāṇatusita’s Bhikkhupātimokkha repository

## Synopsis

The dirctory contains GitHub Actions workflow to build and publish artifacts.

Workflow uses a custom image. Look for the corresponding Dockerfile at the
[sasanarakkha/pali-english-recitations](https://github.com/sasanarakkha/pali-english-recitations/blob/main/.github/)
repository.

The pipeline may be ran locally with the [act](https://github.com/nektos/act)
tool. To do so run `act` at root of the repository with a trigger name
(Docker is required):

```shell
act push -v
```

__Note__: Upload job will normally failed on such a local run.

The `-v` key for verbose output.
