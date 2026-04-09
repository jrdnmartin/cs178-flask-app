# dynamoCode.py
# DynamoDB helpers for storing and reading leaderboard scores.

from datetime import datetime, timezone
from decimal import Decimal
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoRegionError

DYNAMO_TABLE_NAME = 'leaderboard_scores'


def _resolve_region():
    """Pick AWS region from env and fall back to us-east-1 for class projects."""
    return os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION') or 'us-east-1'


def _get_scores_table():
    """Create table resource lazily so module import never hard-fails."""
    try:
        dynamodb_resource = boto3.resource('dynamodb', region_name=_resolve_region())
        return dynamodb_resource.Table(DYNAMO_TABLE_NAME)
    except NoRegionError as exc:
        raise RuntimeError(
            "DynamoDB region is not configured. Set AWS_REGION or AWS_DEFAULT_REGION."
        ) from exc
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Could not initialize DynamoDB table '{DYNAMO_TABLE_NAME}': {exc}") from exc


def _to_decimal(value):
    if value is None:
        return None
    return Decimal(str(value))


def save_score(user_id, player_name, category, score, session_id):
    """Save a completed game score to DynamoDB."""
    scores_table = _get_scores_table()
    achieved_at = datetime.now(timezone.utc).isoformat()
    item = {
        'user_id': str(user_id),
        'player_name': player_name,
        'session_id': session_id,
        'achieved_at': achieved_at,
        'category': category,
        'score': _to_decimal(score),
    }
    scores_table.put_item(Item=item)
    return item


def get_leaderboard(limit=25):
    """Return top scores from DynamoDB sorted by score descending."""
    scores_table = _get_scores_table()
    response = scores_table.scan()
    items = response.get('Items', [])

    while 'LastEvaluatedKey' in response:
        response = scores_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))

    items.sort(key=lambda item: (int(item.get('score', 0)), item.get('achieved_at', '')), reverse=True)
    return items[:limit]


def get_high_scores_by_category(limit_per_category=25):
    """Return grouped leaderboard data with one best score per player per category."""
    scores_table = _get_scores_table()
    response = scores_table.scan()
    items = response.get('Items', [])

    while 'LastEvaluatedKey' in response:
        response = scores_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))

    # Keep only each account's best score in each category.
    best_by_player_category = {}
    for item in items:
        category = item.get('category', 'unknown')
        user_id = str(item.get('user_id', item.get('player_name', 'Guest')))
        score = int(item.get('score', 0))
        achieved_at = item.get('achieved_at', '')
        key = (category, user_id)

        if key not in best_by_player_category:
            best_by_player_category[key] = item
            continue

        current_best = best_by_player_category[key]
        current_score = int(current_best.get('score', 0))
        current_time = current_best.get('achieved_at', '')

        # Replace only if score is better, or same score but newer timestamp.
        if score > current_score or (score == current_score and achieved_at > current_time):
            best_by_player_category[key] = item

    grouped = {
        'population': [],
        'gnp': [],
        'life_expectancy': [],
        'surface_area': [],
        'indep_year': [],
    }

    for (category, _player_name), item in best_by_player_category.items():
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(item)

    for category in grouped:
        grouped[category].sort(
            key=lambda i: (int(i.get('score', 0)), i.get('achieved_at', '')),
            reverse=True,
        )
        grouped[category] = grouped[category][:limit_per_category]

    return grouped
