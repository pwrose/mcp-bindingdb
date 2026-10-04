# CDK2/cyclin A2 chemotype analysis — consolidated prompt

1. Retrieve compounds that bind CDK2/cyclin A2 (only this exact complex, no truncated
   sequences) and have Ki data. Collapse to one record per compound keeping the
   strongest reported Ki.

2. Compute Morgan fingerprints and project the compounds into 2D with t-SNE on a
   Tanimoto distance matrix. Assign chemotypes with ordered SMARTS rules on the ring
   system so each class has a chemically meaningful name, not a cluster index. Create
   two plots sharing the same coordinates: one colored by chemotype, one by Ki.

3. For each chemotype, plot the top 3 compounds by pKi in a 3xn grid. Within each row,
   align the depictions on the substructure that defines the chemotype (template the
   core of the most potent member) and highlight that common substructure. Highlight
   the common substructure in the same color used for that chemotype in the t-SNE
   legend. Put the chemotype name horizontally above each row.

4. Create another plot using the same fingerprints and chemotype annotation with the
   IRIS method (https://github.com/BIDS-Xu-Lab/IRIS). Note, work around this known bug
   (https://github.com/BIDS-Xu-Lab/IRIS/issues/1). Use the affinity (pKi) as the radial
   coordinate.

5. For the pyrido[3,4-d]pyrimidine set, do an R-group decomposition and plot the
   R-groups, ranked within each position by median pKi.

6. Create a self-contained .html file that includes this prompt, the methods, and all
   the figures. Number the prompt steps correctly in the document.

7. In the t-SNE figure and the IRIS figure, make each point clickable. On click, show
   that compound's metadata and its chemical structure. The .html file must remain
   self-contained — no external scripts, stylesheets, or network requests.
