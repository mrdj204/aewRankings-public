"""
Module: stats.py

This module contains API endpoints for displaying rankings, statistics, and graphs.

API Endpoints:
    - /rankings: Retrieve and display the top 10 rankings.
    - /rankings/cards: Retrieve and display rankings for recently wrestled cards.
    - /rankings/extended: Retrieve and display extended rankings.
    - /stats: Retrieve and display stats selector.
    - /stats/{wrestler_division}/{year_key}/{mmr_key}/{stat_division}:
        Retrieve and display stats for specific parameters.
    - /graphs: Retrieve and display graph selector.
    - /graphs_stat/{wrestler_division}/{stat_key}/{division_key}/{winless}: Retrieve and display stat graphs.
    - /graphs_mmr/{wrestler_division}/{mmr_type}/{division_key}/{stat_key}/{winless}: Retrieve and display mmr graphs.
"""
from fastapi import APIRouter

from website.resources import (Any, db, Depends, HTTPException, PERMISSION_ERROR, Request,
                               return_error, SessionData, TemplateResponse)
from website.session import get_session_info
from website.util import html_table
import website.util_matlib as matlib

router = APIRouter()


@router.get("/rankings")
async def top_10_rankings(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to retrieve and display the top 10 rankings.
    """
    session_data: SessionData = session_info["data"]

    output: dict[str, Any] = db.api_rankings_top_10()
    for key, value in output.items():
        output[key] = html_table(value)

    updated_on = f"Last Updated: {db.rankings_updated['date']}<br>{db.rankings_updated['event']}"

    results = {
        "request": request,
        "current_page": "rankings",
        "output": output,
        "updated_on": updated_on,
        "session": session_data,
        "hide_footer": True,
    }
    return TemplateResponse("stats/rankings.html", results)


@router.get("/rankings/cards")
async def recently_wrestled(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to retrieve and display rankings for recent cards.
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_user:
        return await return_error(request, PERMISSION_ERROR)

    output: dict[str, Any] = db.api_rankings_recent_cards()
    for event, wrestlers in output.items():
        wrestlers_api = [{**wrestler.api_ranking_cards()} for wrestler in wrestlers]
        if event == "Champions":
            wrestlers_api = sorted(wrestlers_api, key=lambda x: x['MMR'], reverse=True)
        output[event] = html_table(wrestlers_api, classes="rankings_cards")

    updated_on = f"Rankings Date: {db.rankings_updated['date']}<br>{db.rankings_updated['event']}"

    results = {
        "request": request,
        "current_page": "rankings",
        "output": output,
        "updated_on": updated_on,
        "session": session_data,
        "hide_footer": True,
    }
    return TemplateResponse("stats/rankings_cards.html", results)


@router.get("/rankings/extended/")
async def extended_rankings(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to retrieve and display extended rankings.
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_user:
        return await return_error(request, PERMISSION_ERROR)

    divisions = db.api_rankings_extended()

    results = {
        "request": request,
        "current_page": "rankings",
        "session": session_data,
        "divisions": divisions,
        "hide_footer": True,
    }
    return TemplateResponse("stats/rankings_extended.html", results)


@router.get("/stats/")
async def stats_selector(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to retrieve and display stats selector.
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_user:
        return await return_error(request, PERMISSION_ERROR)

    divisions, years, mmr_keys, division_keys = db.api_stats_keys()

    initial = await get_stats(request, divisions[0], years[0], mmr_keys[0], division_keys[0], session_info)
    initial = initial.body.decode('utf-8')

    results = {
        "request": request,
        "current_page": "stats",
        "session": session_data,
        "divisions": divisions,
        "years": years,
        "mmr_keys": mmr_keys,
        "division_keys": division_keys,
        "initial": initial,
    }
    return TemplateResponse("stats/stats.html", results)


@router.get("/stats/{wrestler_division}/{year_key}/{mmr_key}/{stat_division}")
async def get_stats(request: Request, wrestler_division, year_key, mmr_key, stat_division,
                    session_info: dict = Depends(get_session_info)):
    """
    Endpoint to retrieve and display stats for specific parameters.

    Args:
        request (Request): The request object.
        wrestler_division: Division of the wrestler.
        year_key: Specific year key.
        mmr_key: Specific mmr key.
        stat_division: Specific stat division.
        session_info (dict): Information about the current session.
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_user:
        return await return_error(request, PERMISSION_ERROR)

    division = db.get_division(wrestler_division)
    if not division:
        raise HTTPException(status_code=404, detail=f"{wrestler_division} not found")

    stats = db.api_stats_get(wrestler_division, year_key, mmr_key, stat_division)
    stats = html_table(stats, "stats_table")

    results = {
        "request": request,
        "current_page": "stats",
        "session": session_data,
        "division": division,
        "output": stats,
    }
    return TemplateResponse("stats/stats_get.html", results)


@router.get("/graphs/")
async def graph_selector(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to retrieve and display graph selector.
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_user:
        return await return_error(request, PERMISSION_ERROR)

    (stats_divisions,
     stats_graph_keys,
     stats_division_keys,
     mmr_types,
     mmr_divisions,
     mmr_graph_keys,
     mmr_division_keys
     ) = db.api_graphs_keys()

    results = {
        "request": request,
        "current_page": "graphs",
        "session": session_data,
        "stats_divisions": stats_divisions,
        "stats_division_keys": stats_division_keys,
        "stats_graph_keys": stats_graph_keys,
        "mmr_divisions": mmr_divisions,
        "mmr_types": mmr_types,
        "mmr_division_keys": mmr_division_keys,
        "mmr_graph_keys": mmr_graph_keys,
    }
    return TemplateResponse("stats/graphs.html", results)


@router.get("/graphs_stat/{wrestler_division}/{stat_key}/{division_key}/{winless}")
async def get_stat_graphs(request: Request, wrestler_division, stat_key, division_key, winless,
                          session_info: dict = Depends(get_session_info)):
    """
    Endpoint to retrieve and display stat graphs.

    Args:
        request (Request): The request object.
        wrestler_division: Division for the stats.
        stat_key: Specific stat key.
        division_key: Specific division key.
        winless: Flag to include winless.
        session_info (dict): Information about the current session.
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_user:
        return await return_error(request, PERMISSION_ERROR)

    division = db.get_division(wrestler_division)
    if not division:
        raise HTTPException(status_code=404, detail=f"{wrestler_division} not found")

    include_winless = True if winless == "on" else False
    graphs = matlib.api_graphs(division, division_key, stat_key, include_winless)

    results = {
        "request": request,
        "current_page": "graphs",
        "session": session_data,
        "graphs_html": graphs,
    }
    return TemplateResponse("stats/graphs_get.html", results)


@router.get("/graphs_mmr/{wrestler_division}/{mmr_type}/{division_key}/{stat_key}/{winless}")
async def get_mmr_graphs(request: Request, wrestler_division, mmr_type, division_key, stat_key, winless,
                         session_info: dict = Depends(get_session_info)):
    """
    Endpoint to retrieve and display mmr graphs.

    Args:
        request (Request): The request object.
        wrestler_division: Division for the mmr.
        mmr_type: Specific mmr type.
        division_key: Specific division key.
        stat_key: Specific stat key.
        winless: Flag to include winless.
        session_info (dict): Information about the current session.
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_user:
        return await return_error(request, PERMISSION_ERROR)

    division = db.get_division(wrestler_division)
    if not division:
        raise HTTPException(status_code=404, detail=f"{wrestler_division} not found")

    include_winless = True if winless == "on" else False
    graphs_html = matlib.api_mmr_graphs(division, mmr_type, division_key, stat_key, include_winless)

    results = {
        "request": request,
        "current_page": "graphs",
        "session": session_data,
        "graphs_html": graphs_html,
    }
    return TemplateResponse("stats/graphs_get.html", results)
