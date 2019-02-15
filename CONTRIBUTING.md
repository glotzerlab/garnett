# How to contribute to the project

## Feedback

Issue reports and feature proposals are welcome. Please use the repository issue tracker.

## Contributing code

Code contributions to the glotzformats project are welcomed via pull requests.
Prior any **major** work you should contact the glotzformats developers to ensure that the planned development meshes well with the directions and standards of the project.
All contributors must agree to the Contributor Agreement ([ContributorAgreement.md](ContributorAgreement.md)) before their pull request can be merged as the glotzformats project may be made open-source in the future.

General guidelines:

  * The glotzformats development is based on the [git flow model][gitflow], which means new features should be developed within a feature branch based on the 'develop' branch.
  * Try to avoid external library dependencies.
  * External library dependencies should be *soft* dependencies unless a majority of components share the dependency.
  * All contributed code should pass the default `flake8` checks.
  * New features should be unit tested.

[gitflow]: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow
