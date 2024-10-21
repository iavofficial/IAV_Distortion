# Branch Structure and Guidelines

## General Structure

The project is a fork of the original public repository of the IAV. Only the master branch has been inlcuded in the fork.

All branches other than the "master" is additional and only part of the fork. Unless a pull request has been executed.

## Working on a Feature

### General Guidelines of Feature (Branches)

- To implement additional features or extensions to the project please first create a new feature branch.
- A feature branch should contain all these additions or changes to the project that concern this one feature or are necessary for it to work. 
    - It should work on its own, without needing another feature branch, that is being developed in parallel, to be merged into this feature branch first.
- The feature branch does not need to always represent a working project state.
    - When merging, it should be functional without any new bugs.
- Further branches from the feature branch are allowed, but not recommended. This adds additional complexity to the project and more management overhead due to necessary merges etc..

### Feature Branch Setup:

- name: "feature-[concise feature name]"
- origin: master
- when completed, should be merged to: master

If further branches from this feature branch are required:

- name of feature branch branch: "feature-[concise feature name]:[name]"

### Merge

When work on the feature is done, the following steps should be executed:

- All further branches from the feature branch should be merged into the feature branch or deleted.
- A merge request of the feature branch into the master branch should be opened.
    - Please select an Assignee and a Reviewer. One of these should be the current Head-Developer.
        - The assigned people should try running the branch to detect problems.
        - No merging is allowed without approval.
    - A description of the feature should be included in the merge request.
        - This can be done by referencing an issue.
        - You may also include screenshots or other references that make the feature easier to understand.
- Comments received in the review process should be addressed and the problems fixed.
- If the merge request gets approval, it should be merged.
    