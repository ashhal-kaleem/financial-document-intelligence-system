"""No live SDK/model/provider calls. Tests receipt scope and catalog fail-closed rules."""
import base64
import json
import pytest
import httpx
from src.services import browser_ai as ai
from src.domain.citation import create_citations_from_chunks
from tests.test_production_guards import chunk
from src.core.errors import FDISException
MODEL=next(iter(ai.PUTER_MODELS))

def test_receipt_is_owner_bound_expires_and_rejects_marker_forgery(monkeypatch):
    citations=create_citations_from_chunks([chunk()])
    monkeypatch.setattr(ai.time,'time',lambda:1000)
    receipt=ai.make_receipt('alice',citations,MODEL)
    assert ai.validate_receipt(receipt,'alice','Revenue [1]')==citations
    for user,answer in [('bob','Revenue [1]'),('alice','Revenue [99]'),('alice','No marker')]:
        with pytest.raises(FDISException):ai.validate_receipt(receipt,user,answer)
    body,sig=receipt.split('.')
    parsed=json.loads(base64.urlsafe_b64decode(body+'='*(-len(body)%4)))
    parsed['owner']='bob'
    fake=base64.urlsafe_b64encode(json.dumps(parsed).encode()).decode().rstrip('=')+'.'+sig
    with pytest.raises(FDISException):ai.validate_receipt(fake,'bob','Revenue [1]')
    monkeypatch.setattr(ai.time,'time',lambda:1601)
    with pytest.raises(FDISException):ai.validate_receipt(receipt,'alice','Revenue [1]')

@pytest.mark.asyncio
@pytest.mark.parametrize('costs,ok', [({'tokens':1000000,'prompt':0,'completion':0},True),({'tokens':1000000,'prompt':1,'completion':0},False),({'tokens':1000000,'prompt':0},False),({'tokens':1000000,'prompt':0,'completion':0,'search':1},False)])
async def test_free_catalog_required_and_all_costs_must_be_zero(monkeypatch,costs,ok):
    real=httpx.AsyncClient
    def handler(req):return httpx.Response(200,json={'models':[{'id':MODEL,'costs':costs,'input_cost_key':'prompt','output_cost_key':'completion'}]})
    monkeypatch.setattr(ai.httpx,'AsyncClient',lambda **kw:real(transport=httpx.MockTransport(handler)))
    if ok:await ai.verify_free_model(MODEL)
    else:
        with pytest.raises(FDISException):await ai.verify_free_model(MODEL)

@pytest.mark.asyncio
async def test_unknown_model_fails_without_catalog_request():
    with pytest.raises(FDISException):await ai.verify_free_model('paid-model')

@pytest.mark.parametrize('receipt',['bad','a.b','a.b.c','..',''])
def test_malformed_receipts_rejected(receipt):
    with pytest.raises(FDISException):ai.validate_receipt(receipt,'alice','x [1]')

@pytest.mark.asyncio
async def test_browser_context_requires_explicit_consent_and_allowed_model(monkeypatch):
    from src.api.routes.ask import browser_context
    from src.domain.models import BrowserAIRequest
    from src.core.auth import AuthUser
    from fastapi import HTTPException
    for consent,model in [(False,MODEL),(True,'not-enabled')]:
        with pytest.raises(HTTPException) as exc:
            await browser_context(BrowserAIRequest(question='Revenue?',model=model,consent=consent),AuthUser('alice'))
        assert exc.value.status_code==422

@pytest.mark.asyncio
async def test_browser_no_context_never_checks_catalog_or_calls_provider(monkeypatch):
    from src.api.routes import ask
    from src.domain.models import BrowserAIRequest
    from src.core.auth import AuthUser
    from src.domain.citation import NOT_COVERED_ANSWER
    async def retrieve(**kw):return []
    async def forbidden(*a):raise AssertionError('No catalog call expected')
    monkeypatch.setattr(ask.inference_service.retrieval,'retrieve_relevant_chunks',retrieve)
    monkeypatch.setattr(ask,'verify_free_model',forbidden)
    result=await ask.browser_context(BrowserAIRequest(question='Revenue?',model=MODEL,consent=True),AuthUser('alice'))
    assert result['data']['answer']==NOT_COVERED_ANSWER and result['data']['receipt'] is None

@pytest.mark.asyncio
@pytest.mark.parametrize('visible,accepted',[([],False),(['doc-1'],True)])
async def test_browser_validation_rechecks_visible_documents(monkeypatch,visible,accepted):
    from src.api.routes import ask
    from src.domain.models import BrowserAIValidation
    from src.core.auth import AuthUser
    from fastapi import HTTPException
    citations=create_citations_from_chunks([chunk()])
    doc_id=citations[0].document_id
    async def ids(owner):
        assert owner=='alice'
        return [doc_id] if visible else []
    monkeypatch.setattr(ask.inference_service.retrieval.supabase,'get_visible_document_ids',ids)
    payload=BrowserAIValidation(receipt=ai.make_receipt('alice',citations,MODEL),answer='Revenue [1]')
    if accepted:
        result=await ask.browser_validate(payload,AuthUser('alice'))
        assert result['data']['semantic_support_verified'] is False
    else:
        with pytest.raises(HTTPException) as exc:await ask.browser_validate(payload,AuthUser('alice'))
        assert exc.value.status_code==409
