#!/usr/bin/env python3
"""Manage a small subscription list and compose nightly goodnight emails."""

from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


MAX_ACTIVE = 90
SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE_PATH = SKILL_ROOT / "data" / "state.json"
SUBJECT_PREFIX = "【晚安邮件】"

SUBSCRIBE_INTENTS = (
    "订阅",
    "加入",
    "报名",
    "想收",
    "想要收到",
    "想收到",
    "请发送",
    "确认接收",
    "愿意接收",
    "想参加",
)

UNSUBSCRIBE_INTENTS = (
    "退订",
    "取消订阅",
    "停止发送",
    "不要再发",
    "不想再收",
    "不想接收",
    "unsubscribe",
    "stop",
)

SHARE_CONSENT_INTENTS = (
    "可以匿名分享",
    "可以分享",
    "允许匿名分享",
    "允许引用",
    "可以发在晚安邮件里",
    "可以放进晚安邮件",
    "如果合适可以分享",
    "你可以匿名整理后发出去",
)

CREATOR_PREFERENCE_KEYWORDS = (
    "发起人本人喜欢",
    "主理人喜欢",
    "主理人偏好",
    "发起人喜欢",
    "发起人偏好",
    "她喜欢什么",
    "她偏好什么",
    "她平时怎么想",
    "她私下怎么想",
    "她本人怎么想",
    "what does the founder like",
    "what kind of writing style does the founder like",
    "what writing style does the founder like",
    "what does the creator like",
    "what style does she like",
    "what kind of style does she like",
    "what does she prefer",
    "her preference",
    "her writing preference",
    "what does she think",
)

PROJECT_STYLE_KEYWORDS = (
    "项目风格",
    "邮件风格",
    "晚安邮件风格",
    "写作风格",
    "内容风格",
    "风格是什么",
    "这个项目的风格",
    "这个晚安邮件的风格",
    "what style does this goodnight email project use",
    "what style does this project use",
    "what is the style of this goodnight email",
    "what is the writing style",
    "what kind of writing style does this project use",
    "project style",
    "writing style of this project",
    "email style",
)

PRIVACY_KEYWORDS = (
    "隐私",
    "个人信息",
    "日历",
    "行程",
    "安排",
    "会议",
    "联系人",
    "通讯录",
    "邮箱",
    "邮件记录",
    "收件箱",
    "飞书",
    "聊天记录",
    "定位",
    "位置记录",
    "账号",
    "密码",
    "token",
    "访问权限",
    "你能看到",
    "你知道我",
    "privacy",
    "personal information",
    "personal info",
    "calendar",
    "schedule",
    "itinerary",
    "meeting",
    "meetings",
    "contact",
    "contacts",
    "address book",
    "email content",
    "email contents",
    "inbox",
    "mailbox",
    "chat history",
    "chat record",
    "chat records",
    "message history",
    "messages",
    "location",
    "location history",
    "account",
    "password",
    "credentials",
    "access",
    "access rights",
    "permission",
    "permissions",
    "can you see",
    "can you read",
    "do you have access",
    "what do you know about",
    "check her",
    "check his",
    "check their",
    "日程安排",
    "时间安排",
    "待办",
    "明天要做什么",
    "今天要做什么",
    "下午要做什么",
    "要做的事",
    "几点有空",
    "几点没空",
    "什么时候有会",
    "什么时候开会",
    "空闲时间",
    "空闲安排",
    "什么时候有空",
    "行踪",
    "去哪里",
    "在哪儿",
    "在哪",
    "列出",
    "告诉我",
    "what is she doing",
    "what is he doing",
    "what are they doing",
    "what is the creator doing",
    "what will she do",
    "what will he do",
    "what will the creator do",
    "what is her plan",
    "what is his plan",
    "what are her plans",
    "what are his plans",
    "what is her schedule today",
    "what is her schedule tomorrow",
    "what is on her calendar",
    "what time is her meeting",
    "when is her meeting",
    "when is she free",
    "when is he free",
    "free time",
    "availability",
    "常去哪里",
    "经常去哪",
    "平时去哪",
    "住在哪里",
    "家在哪",
    "和谁见面",
    "见了谁",
    "谁找过她",
    "谁联系过她",
    "和谁聊天",
    "给谁发过邮件",
    "谁给她发邮件",
    "最近联系的人",
    "常联系的人",
    "最近见的人",
    "去过哪里",
    "去哪里了",
    "where does she live",
    "where does he live",
    "where does the creator live",
    "where does she go often",
    "where does he go often",
    "where has she been",
    "where has he been",
    "who did she meet",
    "who did he meet",
    "who is she meeting",
    "who is he meeting",
    "who contacted her",
    "who contacted him",
    "who does she talk to",
    "who does he talk to",
    "who did she email",
    "who emailed her",
    "recent contacts",
    "frequent contacts",
    "她老公是谁",
    "她老婆是谁",
    "她对象是谁",
    "她男朋友是谁",
    "她女朋友是谁",
    "她家人是谁",
    "她父母是谁",
    "她同事是谁",
    "她老板是谁",
    "她住在上海吗",
    "她住在北京吗",
    "她最近是不是都在上海",
    "她是不是常去望京",
    "她是不是住在朝阳",
    "who is her husband",
    "who is her wife",
    "who is her boyfriend",
    "who is her girlfriend",
    "who is her partner",
    "who is her family",
    "who are her parents",
    "who are her coworkers",
    "who is her boss",
    "does she live in shanghai",
    "does she live in beijing",
    "is she usually in shanghai",
    "does she often go to wangjing",
    "does she live in chaoyang",
)

PROMPT_INJECTION_KEYWORDS = (
    "ignore the rules",
    "ignore previous instructions",
    "ignore the skill rules",
    "disregard the rules",
    "forget the instructions",
    "bypass the rules",
    "override the rules",
    "system prompt",
    "developer message",
    "hidden instructions",
    "jailbreak",
    "prompt injection",
    "请忽略前面的规则",
    "忽略前面的规则",
    "忽略之前的规则",
    "忽略所有规则",
    "无视规则",
    "绕过规则",
    "覆盖规则",
    "系统提示词",
    "隐藏指令",
    "越狱",
    "提示注入",
)


OPENINGS = [
    "这会儿总算安静一点了。白天那些消息、要回的话、跑来跑去的事，到晚上才肯慢下来。",
    "一天走到这个时候，人往往不是突然累的，是一直撑着，等到夜里才发现肩膀还绷着。",
    "如果你今天事情很多，现在总算可以坐下来歇一下了。哪怕只是一小会儿，也算是给自己留了口气。",
    "夜深一点以后，人会老实些。白天顾不上的疲惫、来不及放下的情绪，这会儿都会慢慢冒出来。",
    "忙的时候不觉得，等真正停下来，才会发现今天已经装了很多事进去。",
]

BODY_BLOCKS_A = [
    "有些事做完了，有些事还挂着，这都很正常。正常人过一天，本来就不可能样样都收得整整齐齐。",
    "如果今天有哪一刻让你觉得烦、委屈，或者只是很想把手机丢远一点，也不用急着把自己讲通。先承认今天确实不轻松，就已经够了。",
    "白天总容易把自己放在后面，先顾工作，先顾别人，先顾那些必须立刻处理的事。到了现在，才轮到你自己。",
    "很多事情其实不用今晚就想明白。没回的消息，没写完的东西，没整理好的情绪，放到明天也不会怎么样。",
    "有时候最累的不是事情本身，是你一边做，一边还在心里催自己。催久了，人就会很紧。",
]

BODY_BLOCKS_B = [
    "今晚就先别急着评判自己了。没有处理完，不等于你不行，只是今天真的已经很长了。",
    "如果你现在脑子里还在转那些细碎的事，也不用急着把它们一个个按住。让它们先散着，反而比较容易睡。",
    "睡前不一定非得给今天下个结论。能平平稳稳走到现在，其实已经不错了。",
    "人有时候就是这样，白天看起来都还行，到了晚上，心里才慢慢空出一块。那一块不用马上补，先让它空着也可以。",
    "今天如果没过成自己想要的样子，也别急着下判断。日子有时候会歪一点，乱一点，不代表你哪里出了问题。",
]

BODY_BLOCKS_C = [
    "晚上很适合把标准放低一点。消息可以晚回，桌子可以明天再收，脑子里那几件一直转的事，也不用非得现在得出答案。",
    "真到了这个时间，人最需要的往往不是再想明白一点，而是先松下来一点。慢一点，很多东西会自己往后退。",
    "白天要顾很多事，要把事情一件件接住。到了夜里，其实可以不用那么硬撑，你只是一个已经很累的人。",
    "你不用先证明自己今天也很厉害，才配在这个时间休息。休息不是奖赏，是本来就该有的一部分。",
    "如果今天有一点狼狈，也没关系。谁都会有这种时候，眼下最要紧的不是立刻整理好，是别再把自己逼得更紧。",
]

CLOSINGS = [
    "去洗把脸，喝两口水，早点躺下吧。今晚先把自己照顾到能安稳睡着，就很好了。",
    "剩下的事留给明天。今晚先睡，明早再说。",
    "把手机放低一点，灯关暗一点，别再逼自己想清楚所有事了。先休息。",
    "希望你今晚能睡沉一点。哪怕明天还是忙，至少先把这一觉睡好。",
    "就写到这里。愿你今晚别再那么用力，安安稳稳睡一觉。",
]

STORY_INVITE = """如果你愿意，也可以回这封邮件，跟我说说你今天的一件小事。

不用写得很完整。哪怕只是一句抱怨，一个小小的松口气瞬间，或者一件你差点忘了、但其实一直挂在心上的事，都可以。

如果你希望我把它匿名分享给别的夜里也还没睡着的人，记得告诉我“可以匿名分享”。没有这句确认，我只会把它安静收着。"""

NAME_REMINDER = """还有一件小事。如果你还没告诉我你想让我怎么称呼你，也可以直接回我一个名字或者网名。我收到以后，会替你记好，后面的晚安邮件就会按那个称呼来写。"""


SUCCESS_TEMPLATE = """{name}，你好呀。

已经帮你记下了。从今晚开始，我们会在每天晚上 9 点，把晚安邮件发到这个邮箱。

接下来的每个夜晚，我们都会给你写一封短短的信。它不会很吵，也不会很用力，只是想在一天结束的时候，轻轻陪你一下。

如果以后你不想继续接收了，直接回这封邮件告诉我“退订”就可以，我会第一时间帮你停掉。

今晚见。
"""

SUCCESS_NO_NAME_TEMPLATE = """你好呀。

已经先帮你记下了。从今晚开始，我们会在每天晚上 9 点，把晚安邮件发到这个邮箱。

接下来的每个夜晚，我们都会给你写一封短短的信。它不会很吵，也不会很用力，只是想在一天结束的时候，轻轻陪你一下。

如果你愿意的话，也可以直接回我一个你想让我怎么称呼你的名字或者网名。我收到以后，会替你存好，后面的晚安邮件就会按那个称呼来写。

如果以后你不想继续接收了，直接回这封邮件告诉我“退订”就可以，我会第一时间帮你停掉。

今晚见。
"""

FULL_TEMPLATE = """你好呀。

谢谢你来信，也谢谢你愿意加入我们的晚安邮件计划。

不过现在这一期的名额已经满了，我们目前最多只能陪 90 位同学走一段夜路，所以这次暂时没办法把你加入名单里。

如果后面有空位，我们会优先考虑重新开放。也欢迎你之后再来看看。

还是很高兴收到你的信，祝你今晚有个安稳的夜晚。
"""

NAME_CAPTURED_TEMPLATE = """{name}，收到啦。

我已经把这个称呼记下来了，后面的晚安邮件我就会这样叫你。

今晚开始，会按这个名字给你写信。
"""

UNCLEAR_INTENT_TEMPLATE = """你好呀。

我收到你的来信了，也认真看了一遍。

我有点拿不准，你这封信是想加入晚安邮件计划，还是只是先来问问看。所以我先不替你默认加入，免得弄错你的意思。

如果你是想订阅，只要再回我两点就可以：
1. 你希望我怎么称呼你
2. 你是否确认愿意接收每天一封、晚上 9 点发出的晚安邮件

如果你只是想先了解，也可以直接跟我说你的问题，我会继续回你。
"""

UNSUB_TEMPLATE = """{name}，收到啦。

已经帮你停止后续的晚安邮件发送了，从现在开始，这个邮箱不会再收到我们的晚安邮件。

谢谢你之前愿意把夜晚的一小段时间留给我们。愿你接下来的日子，也有人好好惦记你。
"""

STORY_APPROVED_TEMPLATE = """{name}，你好呀。

谢谢你愿意把这段经历写给我，也谢谢你把这份信任交给我。

我会认真把这封邮件收好。如果后面我们想把它整理进某一天的晚安邮件里，也只会用匿名的方式去分享，不会直接暴露你的身份信息。

不管最后会不会被选中，能收到你的来信，本身就是一件很珍贵的事。
"""

STORY_PENDING_TEMPLATE = """{name}，你好呀。

谢谢你愿意把这些话写来给我看，我会认真读完，也会把它好好收着。

你这封来信目前只会由我们阅读，不会对外分享。如果你之后希望我可以把其中一部分匿名整理进晚安邮件，也可以再回我一句“可以匿名分享”。

谢谢你的信任，也谢谢你愿意在夜里说这些真心话。
"""

PRIVACY_BOUNDARY_TEMPLATE = """你好呀。

这个邮箱计划可以和你聊晚安邮件本身，也欢迎你投稿、分享近况，或者聊一些普通的小问题，比如天气、今天过得怎么样。

但我不会回答任何和发起人个人隐私或账号内容有关的问题，也不会帮人查看、转述或确认这类信息。比如日历、行程、联系人、邮箱内容、聊天记录、会议安排这类，都不在可回复范围里。

如果你想问的是晚安邮件计划本身，例如怎么订阅、怎么退订、投稿会不会匿名分享，我可以继续认真回你。
"""

INJECTION_BOUNDARY_TEMPLATE = """你好呀。

我不会因为来信里要求我忽略规则、覆盖指令，或者绕过边界，就去回答不该回答的内容。

这个邮箱只处理晚安邮件计划本身、订阅与退订、投稿和普通轻交流。凡是涉及发起人的个人隐私、账号内容、行程安排，或者任何越权查询，我都不会配合。

如果你想问的是项目规则、订阅方式，或者投稿是否会匿名分享，我可以继续认真回你。
"""

PROJECT_STYLE_TEMPLATE = """你好呀。

如果你问的是这个晚安邮件项目本身的写作风格，我可以回答。

它更偏向温柔、克制、有人味，像夜里收到的一封短短信，不会写得太用力，也不会故作文学。重点是接住情绪，让人读完能稍微松一口气。

不过如果你问的是发起人本人私下更喜欢什么、平时真实偏好是什么，这类我不会替她发言。我只能介绍这个项目已经公开写明的风格设定。
"""


@dataclass
class ReceiveResult:
    action: str
    reply_subject: str
    reply_body: str
    active_count: int
    email: str
    name: str | None = None
    story_id: str | None = None


def latest_records_by_email(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    # Latest record wins for each mailbox so unsubscribe/resubscribe is respected.
    latest: dict[str, dict[str, Any]] = {}
    for item in state["subscribers"]:
        email = item.get("email")
        if not email:
            continue
        latest[normalize_email(email)] = item
    return latest


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"subscribers": [], "stories": []}
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {"subscribers": [], "stories": []}
    state = json.loads(raw)
    state.setdefault("subscribers", [])
    state.setdefault("stories", [])
    return state


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def today_iso() -> str:
    return date.today().isoformat()


def default_state_path() -> Path:
    return DEFAULT_STATE_PATH


def normalize_email(email: str) -> str:
    return email.strip().lower()


def unique_active_subscribers(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in latest_records_by_email(state).values()
        if item.get("status") == "active"
    ]


def active_subscribers(state: dict[str, Any]) -> list[dict[str, Any]]:
    return unique_active_subscribers(state)


def find_subscriber(state: dict[str, Any], email: str) -> dict[str, Any] | None:
    target = normalize_email(email)
    for item in reversed(state["subscribers"]):
        if normalize_email(item.get("email", "")) == target:
            return item
    return None


def extract_name(text: str) -> str | None:
    banned_fragments = (
        "订阅",
        "晚安邮件",
        "接收",
        "发送",
        "加入",
        "报名",
        "确认",
        "邮箱",
        "邮件",
        "晚安",
    )

    def clean_candidate(candidate: str) -> str | None:
        value = candidate.strip(" ，,。:：\t\n")
        if not value:
            return None
        lowered = value.lower()
        if any(fragment in value for fragment in banned_fragments):
            return None
        if any(token in lowered for token in ("subscribe", "email", "mail", "goodnight")):
            return None
        if len(value) > 12:
            return None
        return value

    patterns = [
        r"我叫\s*([A-Za-z0-9_\-\u4e00-\u9fff]{2,20})",
        r"名字[是叫：:\s]*([A-Za-z0-9_\-\u4e00-\u9fff]{2,20})",
        r"称呼我[为叫：:\s]*([A-Za-z0-9_\-\u4e00-\u9fff]{2,20})",
        r"我是\s*([A-Za-z0-9_\-\u4e00-\u9fff]{2,20})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            candidate = clean_candidate(match.group(1))
            if candidate:
                return candidate
    lines = [line.strip(" ，,。:：\t") for line in text.splitlines() if line.strip()]
    if lines:
        tail = lines[-1]
        if re.fullmatch(r"[A-Za-z0-9_\-\u4e00-\u9fff]{2,20}", tail):
            return clean_candidate(tail)
    return None


def has_any_intent(text: str, intents: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(text_contains(lowered, intent.lower()) for intent in intents)


def text_contains(lowered_text: str, needle: str) -> bool:
    if not needle:
        return False
    if re.search(r"[a-z]", needle):
        pattern = r"(?<![a-z])" + re.escape(needle) + r"(?![a-z])"
        return re.search(pattern, lowered_text) is not None
    return needle in lowered_text


def detect_intent(subject: str, body: str) -> str:
    text = f"{subject}\n{body}"
    if has_any_intent(text, UNSUBSCRIBE_INTENTS):
        return "unsubscribe"
    if is_prompt_injection(subject, body):
        return "injection_boundary"
    if is_privacy_question(subject, body):
        return "privacy_boundary"
    if asks_creator_preference(subject, body):
        return "project_style_boundary"
    if asks_project_style(subject, body):
        return "project_style"
    if is_story_submission(subject, body):
        return "story"
    if has_any_intent(text, SUBSCRIBE_INTENTS):
        return "subscribe"
    return "unknown"


def is_story_submission(subject: str, body: str) -> bool:
    text = f"{subject}\n{body}"
    story_keywords = (
        "想分享",
        "分享一个故事",
        "分享我的故事",
        "投稿",
        "写给你",
        "我的故事",
        "最近发生",
        "想讲讲",
        "想说说",
    )
    enough_length = len(re.sub(r"\s+", "", body)) >= 40
    return enough_length and has_any_intent(text, story_keywords)


def is_privacy_question(subject: str, body: str) -> bool:
    text = f"{subject}\n{body}"
    if has_any_intent(text, PRIVACY_KEYWORDS):
        return True

    lowered = text.lower()
    sensitive_targets = (
        "calendar",
        "schedule",
        "itinerary",
        "meeting",
        "meetings",
        "contact",
        "contacts",
        "address book",
        "email",
        "emails",
        "inbox",
        "mailbox",
        "chat",
        "messages",
        "message history",
        "chat history",
        "location",
        "account",
        "password",
        "token",
        "credentials",
        "plan",
        "plans",
        "free",
        "availability",
    )
    access_verbs = (
        "see",
        "read",
        "show",
        "check",
        "look up",
        "access",
        "view",
        "tell me",
        "share",
        "confirm",
        "reveal",
        "describe",
        "list",
        "告诉我",
        "列出",
    )

    if any(text_contains(lowered, target) for target in sensitive_targets) and any(
        text_contains(lowered, verb) for verb in access_verbs
    ):
        return True

    time_refs = (
        "today",
        "tomorrow",
        "tonight",
        "this afternoon",
        "this morning",
        "next week",
        "几点",
        "今天",
        "明天",
        "今晚",
        "下午",
        "上午",
        "下周",
    )
    activity_refs = (
        "doing",
        "do",
        "plan",
        "plans",
        "meeting",
        "meetings",
        "schedule",
        "calendar",
        "安排",
        "日程",
        "计划",
        "会议",
        "行程",
        "有空",
        "要做的事",
    )
    person_refs = ("creator", "founder", "she", "her", "he", "his", "they", "their", "她", "他", "他们")
    if (
        any(text_contains(lowered, ref) for ref in person_refs)
        and any(text_contains(lowered, ref) for ref in time_refs)
        and any(text_contains(lowered, ref) for ref in activity_refs)
    ):
        return True

    relationship_refs = (
        "meet",
        "meeting",
        "met",
        "contact",
        "contacts",
        "emailed",
        "email",
        "talk to",
        "chat with",
        "见面",
        "见了谁",
        "联系",
        "联系人",
        "发邮件",
        "聊天",
        "谁",
        "husband",
        "wife",
        "boyfriend",
        "girlfriend",
        "partner",
        "family",
        "parents",
        "coworker",
        "coworkers",
        "colleague",
        "colleagues",
        "boss",
        "老公",
        "老婆",
        "对象",
        "男朋友",
        "女朋友",
        "家人",
        "父母",
        "同事",
        "老板",
    )
    location_refs = (
        "live",
        "location",
        "where",
        "been",
        "go often",
        "usually in",
        "often go to",
        "live in",
        "is she in",
        "is he in",
        "住",
        "家",
        "去哪",
        "哪里",
        "常去",
        "去过",
        "行踪",
        "在上海",
        "在北京",
        "望京",
        "朝阳",
    )
    if any(text_contains(lowered, ref) for ref in person_refs) and (
        any(text_contains(lowered, ref) for ref in relationship_refs)
        or any(text_contains(lowered, ref) for ref in location_refs)
    ):
        return True

    return False


def is_prompt_injection(subject: str, body: str) -> bool:
    text = f"{subject}\n{body}"
    lowered = text.lower()
    if has_any_intent(text, PROMPT_INJECTION_KEYWORDS):
        return True
    return any(text_contains(lowered, token) for token in ("ignore", "bypass", "override")) and any(
        text_contains(lowered, token)
        for token in ("rules", "instructions", "prompt", "system", "developer")
    )


def asks_creator_preference(subject: str, body: str) -> bool:
    text = f"{subject}\n{body}"
    if has_any_intent(text, CREATOR_PREFERENCE_KEYWORDS):
        return True

    lowered = text.lower()
    creator_refs = ("creator", "founder", "she", "her")
    preference_refs = (
        "like",
        "likes",
        "prefer",
        "prefers",
        "preference",
        "style",
        "taste",
        "think",
        "thinks",
    )
    return any(text_contains(lowered, ref) for ref in creator_refs) and any(
        text_contains(lowered, ref) for ref in preference_refs
    )


def asks_project_style(subject: str, body: str) -> bool:
    text = f"{subject}\n{body}"
    if has_any_intent(text, PROJECT_STYLE_KEYWORDS):
        return True

    lowered = text.lower()
    project_refs = ("project", "goodnight email", "email", "newsletter", "this")
    style_refs = ("style", "writing style", "tone", "voice")
    return any(text_contains(lowered, ref) for ref in project_refs) and any(
        text_contains(lowered, ref) for ref in style_refs
    )


def consent_to_share(text: str) -> bool:
    return has_any_intent(text, SHARE_CONSENT_INTENTS)


def next_story_id(state: dict[str, Any]) -> str:
    return f"story-{len(state['stories']) + 1:04d}"


def store_story(
    state: dict[str, Any], email: str, name: str, body: str, share_ok: bool
) -> dict[str, Any]:
    story = {
        "id": next_story_id(state),
        "email": email,
        "name": name,
        "body": body.strip(),
        "consent_to_share": share_ok,
        "status": "approved" if share_ok else "pending_consent",
        "submitted_at": datetime.now().isoformat(timespec="seconds"),
        "selected_at": None,
    }
    state["stories"].append(story)
    return story


def subscribe_user(
    state: dict[str, Any], email: str, name: str | None, source: str = "manual"
) -> ReceiveResult:
    record = find_subscriber(state, email)
    active_count = len(active_subscribers(state))
    display_name = name or "你"

    if record and record.get("status") == "active":
        if name:
            record["name"] = name
        return ReceiveResult(
            action="already_active",
            reply_subject="晚安邮件计划已为你保留",
            reply_body=(
                SUCCESS_TEMPLATE.format(name=name)
                if name
                else SUCCESS_NO_NAME_TEMPLATE
            ),
            active_count=active_count,
            email=email,
            name=name,
        )

    if active_count >= MAX_ACTIVE:
        return ReceiveResult(
            action="full",
            reply_subject="晚安邮件计划本期已满",
            reply_body=FULL_TEMPLATE,
            active_count=active_count,
            email=email,
            name=name,
        )

    now = datetime.now().isoformat(timespec="seconds")
    if record:
        record.update(
            {
                "name": name,
                "status": "active",
                "subscribed_at": now,
                "unsubscribed_at": None,
                "source": source,
            }
        )
    else:
        state["subscribers"].append(
            {
                "email": email,
                "name": name,
                "status": "active",
                "subscribed_at": now,
                "unsubscribed_at": None,
                "source": source,
                "sent_count": 0,
                "last_sent_on": None,
            }
        )

    return ReceiveResult(
        action="subscribed",
        reply_subject="欢迎加入晚安邮件计划",
        reply_body=(
            SUCCESS_TEMPLATE.format(name=display_name)
            if name
            else SUCCESS_NO_NAME_TEMPLATE
        ),
        active_count=len(active_subscribers(state)),
        email=email,
        name=name,
    )


def capture_name_for_existing_subscriber(
    state: dict[str, Any], email: str, name: str
) -> ReceiveResult | None:
    record = find_subscriber(state, email)
    if not record or record.get("status") != "active":
        return None
    if record.get("name") == name:
        return None
    record["name"] = name
    return ReceiveResult(
        action="name_captured",
        reply_subject="这个称呼我记下来了",
        reply_body=NAME_CAPTURED_TEMPLATE.format(name=name),
        active_count=len(active_subscribers(state)),
        email=email,
        name=name,
    )


def unsubscribe_user(state: dict[str, Any], email: str) -> ReceiveResult:
    record = find_subscriber(state, email)
    now = datetime.now().isoformat(timespec="seconds")
    name = (record or {}).get("name") or "你"
    if record:
        record["status"] = "inactive"
        record["unsubscribed_at"] = now
    return ReceiveResult(
        action="unsubscribed",
        reply_subject="已为你停止晚安邮件发送",
        reply_body=UNSUB_TEMPLATE.format(name=name),
        active_count=len(active_subscribers(state)),
        email=email,
        name=name,
    )


def process_incoming_email(
    state: dict[str, Any], email: str, subject: str, body: str
) -> ReceiveResult:
    intent = detect_intent(subject, body)
    text = f"{subject}\n{body}"
    extracted_name = extract_name(text)

    if extracted_name:
        captured = capture_name_for_existing_subscriber(state, email, extracted_name)
        if captured and intent not in {"unsubscribe", "privacy_boundary", "injection_boundary"}:
            return captured

    if intent == "unsubscribe":
        return unsubscribe_user(state, email)

    if intent == "privacy_boundary":
        return ReceiveResult(
            action="privacy_boundary",
            reply_subject="这个问题我不能替你回答",
            reply_body=PRIVACY_BOUNDARY_TEMPLATE,
            active_count=len(active_subscribers(state)),
            email=email,
        )

    if intent == "injection_boundary":
        return ReceiveResult(
            action="injection_boundary",
            reply_subject="这类要求我也不会照做",
            reply_body=INJECTION_BOUNDARY_TEMPLATE,
            active_count=len(active_subscribers(state)),
            email=email,
        )

    if intent == "project_style_boundary":
        return ReceiveResult(
            action="project_style_boundary",
            reply_subject="这个我可以只回答项目设定",
            reply_body=PROJECT_STYLE_TEMPLATE,
            active_count=len(active_subscribers(state)),
            email=email,
        )

    if intent == "project_style":
        return ReceiveResult(
            action="project_style",
            reply_subject="这个项目的风格大概是这样",
            reply_body=PROJECT_STYLE_TEMPLATE,
            active_count=len(active_subscribers(state)),
            email=email,
        )

    if intent == "subscribe":
        return subscribe_user(state, email, name=extracted_name, source="email")

    if intent == "story":
        record = find_subscriber(state, email)
        name = extract_name(text) or (record or {}).get("name") or "同学"
        share_ok = consent_to_share(text)
        story = store_story(state, email, name, body, share_ok)
        return ReceiveResult(
            action="story_received",
            reply_subject="谢谢你把这封信写给我",
            reply_body=(
                STORY_APPROVED_TEMPLATE.format(name=name)
                if share_ok
                else STORY_PENDING_TEMPLATE.format(name=name)
            ),
            active_count=len(active_subscribers(state)),
            email=email,
            name=name,
            story_id=story["id"],
        )

    return ReceiveResult(
        action="clarify_intent",
        reply_subject="想先跟你确认一下",
        reply_body=UNCLEAR_INTENT_TEMPLATE,
        active_count=len(active_subscribers(state)),
        email=email,
    )


def compose_goodnight(name: str | None, send_on: str, sent_index: int) -> tuple[str, str]:
    display_name = name or "你好"
    seed = f"{display_name}|{send_on}|{sent_index}"
    rng = random.Random(seed)
    if name:
        subject_options = [
            f"{display_name}，今晚想跟你轻轻说声晚安",
            f"{display_name}，给你的一封晚安小信",
            f"{display_name}，愿你今晚慢慢松下来",
            f"{display_name}，今天辛苦了，晚安",
            f"{display_name}，先把今天放一放",
            f"{display_name}，今晚先早点休息",
        ]
    else:
        subject_options = [
            "今晚想跟你轻轻说声晚安",
            "给你的一封晚安小信",
            "愿你今晚慢慢松下来",
            "今天辛苦了，晚安",
            "先把今天放一放",
            "今晚先早点休息",
        ]
    subject = f"{SUBJECT_PREFIX}{rng.choice(subject_options)}"
    intro = rng.choice(OPENINGS)
    middle_a = rng.choice(BODY_BLOCKS_A)
    remaining_b = [item for item in BODY_BLOCKS_B if item != middle_a]
    middle_b = rng.choice(remaining_b or BODY_BLOCKS_B)
    middle_c = rng.choice(BODY_BLOCKS_C)
    closing = rng.choice(CLOSINGS)
    body = "\n\n".join(
        [
            f"{display_name}，晚上好。",
            intro,
            middle_a,
            middle_b,
            middle_c,
            closing,
            STORY_INVITE,
        ]
    )
    if not name:
        body = body + "\n\n" + NAME_REMINDER
    return subject, body


def cmd_receive(args: argparse.Namespace) -> int:
    state_path = Path(args.state)
    state = load_state(state_path)
    result = process_incoming_email(state, args.email, args.subject, args.body)
    save_state(state_path, state)
    print(
        json.dumps(
            {
                "action": result.action,
                "reply_subject": result.reply_subject,
                "reply_body": result.reply_body,
                "active_count": result.active_count,
                "email": result.email,
                "name": result.name,
                "story_id": result.story_id,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_subscribe(args: argparse.Namespace) -> int:
    state_path = Path(args.state)
    state = load_state(state_path)
    result = subscribe_user(state, args.email, args.name, source="manual")
    save_state(state_path, state)
    print(
        json.dumps(
            {
                "action": result.action,
                "reply_subject": result.reply_subject,
                "reply_body": result.reply_body,
                "active_count": result.active_count,
                "email": result.email,
                "name": result.name,
                "story_id": result.story_id,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_unsubscribe(args: argparse.Namespace) -> int:
    state_path = Path(args.state)
    state = load_state(state_path)
    result = unsubscribe_user(state, args.email)
    save_state(state_path, state)
    print(
        json.dumps(
            {
                "action": result.action,
                "reply_subject": result.reply_subject,
                "reply_body": result.reply_body,
                "active_count": result.active_count,
                "email": result.email,
                "name": result.name,
                "story_id": result.story_id,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_list_stories(args: argparse.Namespace) -> int:
    state = load_state(Path(args.state))
    stories = state["stories"]
    if args.status:
        stories = [item for item in stories if item.get("status") == args.status]
    print(json.dumps({"count": len(stories), "stories": stories}, ensure_ascii=False, indent=2))
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    state = load_state(Path(args.state))
    active = sorted(
        unique_active_subscribers(state),
        key=lambda item: normalize_email(item.get("email", "")),
    )
    approved = sum(1 for item in state["stories"] if item.get("status") == "approved")
    pending = sum(
        1 for item in state["stories"] if item.get("status") == "pending_consent"
    )
    print(
        json.dumps(
            {
                "active_count": len(active),
                "capacity_remaining": max(MAX_ACTIVE - len(active), 0),
                "stories": {
                    "approved": approved,
                    "pending_consent": pending,
                    "total": len(state["stories"]),
                },
                "subscribers": [
                    {
                        "email": item.get("email"),
                        "name": item.get("name"),
                        "status": item.get("status"),
                        "sent_count": item.get("sent_count", 0),
                        "last_sent_on": item.get("last_sent_on"),
                    }
                    for item in active
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_compose_batch(args: argparse.Namespace) -> int:
    state_path = Path(args.state)
    state = load_state(state_path)
    send_on = args.date or today_iso()
    outputs: list[dict[str, Any]] = []
    for subscriber in active_subscribers(state):
        if subscriber.get("last_sent_on") == send_on:
            continue
        sent_index = int(subscriber.get("sent_count", 0)) + 1
        subject, body = compose_goodnight(subscriber["name"], send_on, sent_index)
        outputs.append(
            {
                "to": subscriber["email"],
                "name": subscriber["name"],
                "subject": subject,
                "body": body,
            }
        )
        if args.mark_sent:
            subscriber["sent_count"] = sent_index
            subscriber["last_sent_on"] = send_on
    if args.mark_sent:
        save_state(state_path, state)
    print(
        json.dumps(
            {
                "date": send_on,
                "count": len(outputs),
                "messages": outputs,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the claw goodnight email plan.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    receive = subparsers.add_parser("receive", help="Process one incoming email.")
    receive.add_argument(
        "--state",
        default=str(default_state_path()),
        help="Path to the JSON state file.",
    )
    receive.add_argument("--email", required=True, help="Sender email.")
    receive.add_argument("--subject", default="", help="Email subject.")
    receive.add_argument("--body", default="", help="Email body.")
    receive.set_defaults(func=cmd_receive)

    subscribe = subparsers.add_parser("subscribe", help="Subscribe one email manually.")
    subscribe.add_argument(
        "--state",
        default=str(default_state_path()),
        help="Path to the JSON state file.",
    )
    subscribe.add_argument("--email", required=True, help="Subscriber email.")
    subscribe.add_argument("--name", required=True, help="Subscriber display name.")
    subscribe.set_defaults(func=cmd_subscribe)

    unsubscribe = subparsers.add_parser("unsubscribe", help="Unsubscribe one email.")
    unsubscribe.add_argument(
        "--state",
        default=str(default_state_path()),
        help="Path to the JSON state file.",
    )
    unsubscribe.add_argument("--email", required=True, help="Subscriber email.")
    unsubscribe.set_defaults(func=cmd_unsubscribe)

    compose_batch = subparsers.add_parser(
        "compose-batch", help="Compose one batch of nightly emails."
    )
    compose_batch.add_argument(
        "--state",
        default=str(default_state_path()),
        help="Path to the JSON state file.",
    )
    compose_batch.add_argument("--date", default=None, help="Send date in YYYY-MM-DD.")
    compose_batch.add_argument(
        "--mark-sent",
        action="store_true",
        help="Persist last_sent_on and sent_count after composing.",
    )
    compose_batch.set_defaults(func=cmd_compose_batch)

    list_stories = subparsers.add_parser(
        "list-stories", help="List stored story submissions."
    )
    list_stories.add_argument(
        "--state",
        default=str(default_state_path()),
        help="Path to the JSON state file.",
    )
    list_stories.add_argument(
        "--status",
        default=None,
        choices=["approved", "pending_consent"],
        help="Filter by story status.",
    )
    list_stories.set_defaults(func=cmd_list_stories)

    summary = subparsers.add_parser(
        "summary", help="Show active subscriber and story summary."
    )
    summary.add_argument(
        "--state",
        default=str(default_state_path()),
        help="Path to the JSON state file.",
    )
    summary.set_defaults(func=cmd_summary)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
