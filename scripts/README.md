## Explicit Docusaurus version in API Reference links
As the API Reference doc files are generated with sphinx and later manipulated with beautiful soup, links for a newly cut version of docusaurus will not be updated correctly automatically. The purpose of this script is to be able to update all the links of API Reference mdx files inside `versioned_docs` folder.

### How to use

1. Cut new version of Docusaurus first
2. Run the script passing as a param the last archived version (so for example if old version was 1.1.0 and you release version 1.2.0 after cut, you should pass 1.1.0 as a parameter), e.g.:
   `python3 explicit_docusaurus_version_in_api_reference_links.py 1.1.0`.
   This will result on the internal links on version 1.1.0 folder to have the version explicitly set in the links so they won't break when the page is up
