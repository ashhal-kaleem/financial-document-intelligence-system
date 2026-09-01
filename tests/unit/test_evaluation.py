"""Unit tests for the evaluation scripts logic."""
import pytest
from scripts.evaluate_retrieval import calculate_mrr, calculate_recall_at_k

def test_calculate_mrr():
    # ranks: 1, 2, 4 -> 1/1 + 1/2 + 1/4 = 1.75 / 3 = 0.58333...
    ranks = [1, 2, 4]
    mrr = calculate_mrr(ranks)
    assert round(mrr, 5) == 0.58333

def test_calculate_mrr_empty():
    assert calculate_mrr([]) == 0.0

def test_calculate_recall_at_k():
    ranks = [1, 2, 6, 11]
    
    # K=1
    assert calculate_recall_at_k(ranks, 1) == 0.25
    
    # K=3
    assert calculate_recall_at_k(ranks, 3) == 0.50
    
    # K=5
    assert calculate_recall_at_k(ranks, 5) == 0.50
    
    # K=10
    assert calculate_recall_at_k(ranks, 10) == 0.75
    
    # K=20
    assert calculate_recall_at_k(ranks, 20) == 1.00

def test_calculate_recall_at_k_empty():
    assert calculate_recall_at_k([], 5) == 0.0

from scripts.evaluate_answers import fact_in_text as check_fact_in_text

def test_check_fact_in_text():
    assert check_fact_in_text("123 million", "The revenue was 123 million dollars.")
    assert check_fact_in_text("123 million", "The revenue was 123 MILLION dollars.")
    assert not check_fact_in_text("123 million", "The revenue was 124 million dollars.")

