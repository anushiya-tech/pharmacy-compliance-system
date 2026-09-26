\# Prescription-Sale Matching Module



\## Purpose



The matching module compares medicines extracted from a prescription with medicines recorded in a pharmacy sale.



It identifies:



\- Matched medicines

\- Missing medicines

\- Quantity mismatches

\- Extra medicines

\- Overall compliance status



\## Processing Flow



Prescription Entity Extraction

&#x20;       ↓

Normalized Medicine Data

&#x20;       ↓

Prescription-Sale Matching

&#x20;       ↓

Item-Level Comparison

&#x20;       ↓

Compliance Report



\## Main Components



\### models.py



Defines the data structures used by the matching engine.



\#### SaleItem



Represents a medicine sold by the pharmacy.



Fields include:



\- Medicine name

\- Normalized medicine name

\- Strength value

\- Strength unit

\- Dosage form

\- Quantity



\#### MatchResult



Represents the result of comparing one prescription item with a sale item.



\#### MatchingReport



Contains the complete matching result.



It provides:



\- Matched items

\- Missing items

\- Quantity mismatches

\- Extra sale items

\- Total prescription item count

\- Overall compliance status



\### matcher.py



Contains the core matching algorithm.



The matcher compares:



1\. Normalized medicine name

2\. Strength value

3\. Strength unit

4\. Dosage form

5\. Quantity



\### service.py



Provides the service layer used by other modules.



It connects prescription entity extraction with the matching engine.



\### cli.py



Provides a command-line interface for loading pharmacy sale data.



\### \_\_init\_\_.py



Exposes the main matching classes and service.



\## Matching Rules



A prescription medicine is considered matched when its normalized medicine identity is compatible with the sale item.



Strength and dosage form are also checked when both records provide those values.



Quantity differences are reported separately.



\## Compliance Logic



A prescription-sale transaction is considered compliant when:



\- No prescription medicine is missing

\- No quantity mismatch exists

\- No extra sale medicine exists



Otherwise the report is marked as non-compliant.



\## Testing



The matching module is tested using:



```powershell

python -m unittest tests\\test\_matching.py -v

