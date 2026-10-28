# VeriRAG demonstration project

## Abstract
This synthetic demonstration paper describes VeriRAG, a retrieval and citation checking design for scientific question answering. It is a fictional teaching example, not published research. No experiments were executed and no measured improvements are claimed.

## 1. Introduction
Retrieval augmented generation retrieves document passages before producing an answer. A citation can point to a relevant document while still failing to support the specific generated claim. We propose checking each answer claim against the retrieved passage and retaining its document and page provenance.

## 2. Method
The proposed system splits searchable papers into passages, ranks passages with BM25, decomposes an answer into individual claims, and checks whether a supporting passage exists. Unsupported statements are flagged for human review. The implementation should preserve the original passage alongside each citation.

## 3. Proposed Evaluation
Use a held-out test set of scientific questions with manually annotated supporting passages. Compare BM25 retrieval with a dense retrieval baseline under identical passage budgets. Record precision, recall, citation support rate, and latency. These are proposed metrics; this paper contains no measured results.

## 4. Limitations
However, the method fails on multilingual queries because only English tokenization is specified. The current design lacks a procedure for resolving contradictory evidence across papers. Citation checks may fail when the supporting evidence spans several passages. Future work should evaluate robustness to noisy PDF extraction and missing page metadata.

## 5. Conclusion
Claim-level citation review can make evidence inspection easier. This source intentionally omits component comparison experiments and environment setup instructions so reviewers can demonstrate documentation gap detection. All proposed changes require implementation and empirical validation.