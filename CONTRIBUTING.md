# How to contribute to the project

## Feedback

Issue reports and feature proposals are welcome. Please use the repository issue tracker.

## Contributing code

Code contributions to the garnett project are welcomed via pull requests.
Contact the garnett developers before you begin **major** work to ensure that the planned development meshes well with the directions and standards of the project.
All contributors must agree to the Contributor Agreement ([ContributorAgreement.md](ContributorAgreement.md)) before their pull request can be merged as the garnett project may be made open-source in the future.

General guidelines:

  * Use the [OneFlow](https://www.endoflineblog.com/oneflow-a-git-branching-model-and-workflow) model of development:
      - Both new features and bug fixes should be developed in branches based on `master`.
      - Hotfixes (critical bugs that need to be released *fast*) should be developed in a branch based on the latest tagged release.
  * Try to avoid external library dependencies.
  * External library dependencies should be *soft* dependencies unless a majority of components share the dependency.
  * All contributed code should pass the default `flake8` checks.
  * New features should be unit tested.

[gitflow]: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow
