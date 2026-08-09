# -*- coding: utf-8 -*-
"""
Three Kingdoms Werewolf — китайская версия игры Werewolf, основанная на AgentScope.
Интеграция персонажей из «Романа трех королевств» и традиционного игрового процесса убийства оборотней.
"""
import asyncio
import os
import random
from typing import List, Dict, Optional

from agentscope.agent import ReActAgent
from agentscope.model import DashScopeChatModel
from agentscope.pipeline import MsgHub, sequential_pipeline, fanout_pipeline
from agentscope.formatter import DashScopeMultiAgentFormatter

from prompt_cn import ChinesePrompts
from game_roles import GameRoles
from structured_output_cn import (
    DiscussionModelCN,
    get_vote_model_cn,
    WitchActionModelCN,
    get_seer_model_cn,
    get_hunter_model_cn,
    WerewolfKillModelCN
)
from utils_cn import (
    check_winning_cn,
    majority_vote_cn,
    get_chinese_name,
    format_player_list,
    GameModerator,
    MAX_GAME_ROUND,
    MAX_DISCUSSION_ROUND,
)


class ThreeKingdomsWerewolfGame:
    """Основная категория: игра об убийстве оборотней Троецарствия"""
    
    def __init__(self):
        self.players: Dict[str, ReActAgent] = {}
        self.roles: Dict[str, str] = {}
        self.moderator = GameModerator()
        self.alive_players: List[ReActAgent] = []
        self.werewolves: List[ReActAgent] = []
        self.villagers: List[ReActAgent] = []
        self.seer: List[ReActAgent] = []
        self.witch: List[ReActAgent] = []
        self.hunter: List[ReActAgent] = []
        
        # Статус ведьмы
        self.witch_has_antidote = True
        self.witch_has_poison = True
        
    async def create_player(self, role: str, character: str) -> ReActAgent:
        """Создайте игрока с предысторией Трех Королевств."""
        name = get_chinese_name(character)
        self.roles[name] = role
        
        agent = ReActAgent(
            name=name,
            sys_prompt=ChinesePrompts.get_role_prompt(role, character),
            model=DashScopeChatModel(
                model_name="qwen-max",
                api_key=os.environ["DASHSCOPE_API_KEY"],
                enable_thinking=True,
            ),
            formatter=DashScopeMultiAgentFormatter(),
        )
        
        # Подтверждение ролевой личности
        await agent.observe(
            await self.moderator.announce(
                f"【{name}】Вы играете в {GameRoles.get_role_desc(role)} в этом убийстве оборотня в Трех Королевствах,"
                f"Ваш персонаж – {character}. {GameRoles.get_role_ability(роль)}"
            )
        )
        
        self.players[name] = agent
        return agent
    
    async def setup_game(self, player_count: int = 6):
        """Настроить игру"""
        print("🎮 Начните настройку игры «Троецарствие оборотней»…")
        
        # Получить конфигурацию роли
        roles = GameRoles.get_standard_setup(player_count)
        characters = random.sample([
            "Лю Бэй", "Гуань Юй", "Чжан Фэй", "Чжугэ Лян", "Чжао Юн",
            "Цао Цао", "Сыма Йи", "Чжоу Ю", "Сунь Цюань"
        ], player_count)
        
        # Создать игрока
        for i, (role, character) in enumerate(zip(roles, characters)):
            agent = await self.create_player(role, character)
            self.alive_players.append(agent)
            
            # Приписан к соответствующему лагерю
            if role == "оборотень":
                self.werewolves.append(agent)
            elif role == "пророк":
                self.seer.append(agent)
            elif role == "ведьма":
                self.witch.append(agent)
            elif role == "охотник":
                self.hunter.append(agent)
            else:
                self.villagers.append(agent)
        
        # Объявление о начале игры
        await self.moderator.announce(
            f"Игра по убийству оборотней Троецарствия начинается! Участники: {format_player_list(self.alive_players)}"
        )
        
        print(f"✅ Настройка игры завершена, всего игроков: {len(self.alive_players)}")
    
    async def werewolf_phase(self, round_num: int):
        """стадия оборотня"""
        if not self.werewolves:
            return None
            
        await self.moderator.announce(f"🐺 Оборотни, пожалуйста, откройте глаза и выберите цель, которую хотите убить сегодня вечером...")
        
        # обсуждение оборотней
        async with MsgHub(
            self.werewolves,
            enable_auto_broadcast=True,
            announcement=await self.moderator.announce(
                f"Оборотни, пожалуйста, обсудите, кого вы хотите убить сегодня вечером. Выжившие игроки: {format_player_list(self.alive_players)}"
            ),
        ) as werewolves_hub:
            # стадия обсуждения
            for _ in range(MAX_DISCUSSION_ROUND):
                for wolf in self.werewolves:
                    await wolf(structured_model=DiscussionModelCN)
            
            # голосовать за убийство
            werewolves_hub.set_auto_broadcast(False)
            kill_votes = await fanout_pipeline(
                self.werewolves,
                msg=await self.moderator.announce("Пожалуйста, выберите цель, которую хотите убить"),
                structured_model=WerewolfKillModelCN,
                enable_gather=False,
            )
            
            # Статистическое голосование
            votes = {}
            for i, vote_msg in enumerate(kill_votes):
                # Проверьте, имеет ли значение voice_msg значение None или существуют ли метаданные.
                if vote_msg is not None and hasattr(vote_msg, 'metadata') and vote_msg.metadata is not None:
                    votes[self.werewolves[i].name] = vote_msg.metadata.get("target")
                else:
                    # Если возврат недействителен, случайным образом выберите цель
                    print(f"⚠️ Голосование за убийство {self.werewolves[i].name} недействительно, цель выбирается случайным образом.")
                    import random
                    valid_targets = [p.name for p in self.alive_players if p.name not in [w.name for w in self.werewolves]]
                    votes[self.werewolves[i].name] = random.choice(valid_targets) if valid_targets else None
            
            killed_player, _ = majority_vote_cn(votes)
            return killed_player
    
    async def seer_phase(self):
        """этап пророка"""
        if not self.seer:
            return
            
        seer_agent = self.seer[0]
        await self.moderator.announce("🔮 Пророк, пожалуйста, открой глаза и выбери игрока, которого хочешь проверить...")
        
        check_result = await seer_agent(
            structured_model=get_seer_model_cn(self.alive_players)
        )

        # Проверьте, действителен ли возвращенный результат
        if check_result is None or not hasattr(check_result, 'metadata') or check_result.metadata is None:
            print(f"⚠️ Проверка оракула не удалась, пропустите этот этап")
            return

        target_name = check_result.metadata.get("target")
        if not target_name:
            print(f"⚠️Пророк не выбрал цель проверки и пропускает этот этап")
            return

        target_role = self.roles.get(target_name, "сельский житель")
        
        # Сообщите оракулу о результате
        result_msg = f"Результат проверки: {target_name} — {'Оборотень', если target_role == 'Оборотень', иначе 'Хороший парень'}"
        await seer_agent.observe(await self.moderator.announce(result_msg))
    
    async def witch_phase(self, killed_player: str):
        """сцена ведьмы"""
        if not self.witch:
            return killed_player, None
            
        witch_agent = self.witch[0]
        await self.moderator.announce("🧙‍♀️ Ведьма, пожалуйста, открой глаза...")
        
        # Сообщите ведьме о ее смерти
        death_info = f"{killed_player} был убит сегодня вечером оборотнем" if killed_player else "Сегодня вечером все безопасно"
        await witch_agent.observe(await self.moderator.announce(death_info))
        
        # ведьма
        witch_action = await witch_agent(structured_model=WitchActionModelCN)

        saved_player = None
        poisoned_player = None

        # Проверьте, действителен ли возвращенный результат
        if witch_action is None or not hasattr(witch_action, 'metadata') or witch_action.metadata is None:
            print(f"⚠️ Если действие ведьмы провалится, это будет расценено как не использование навыков.")
        else:
            if witch_action.metadata.get("use_antidote") and self.witch_has_antidote:
                if killed_player:
                    saved_player = killed_player
                    self.witch_has_antidote = False
                    await witch_agent.observe(await self.moderator.announce(f"Вы использовали противоядие, чтобы спасти {killed_player}."))

            if witch_action.metadata.get("use_poison") and self.witch_has_poison:
                poisoned_player = witch_action.metadata.get("target_name")
                if poisoned_player:
                    self.witch_has_poison = False
                    await witch_agent.observe(await self.moderator.announce(f"Вы использовали яд, чтобы убить {poisoned_player}"))
        
        # Определите последнего игрока, который умрет
        final_killed = killed_player if not saved_player else None
        
        return final_killed, poisoned_player
    
    async def hunter_phase(self, shot_by_hunter: str):
        """этап охотника"""
        if not self.hunter:
            return None
            
        hunter_agent = self.hunter[0]
        if hunter_agent.name == shot_by_hunter:
            await self.moderator.announce("🏹 Охотник активирует навыки, чтобы отобрать игрока...")
            
            hunter_action = await hunter_agent(
                structured_model=get_hunter_model_cn(self.alive_players)
            )

            # Проверьте, действителен ли возвращенный результат
            if hunter_action is None or not hasattr(hunter_action, 'metadata') or hunter_action.metadata is None:
                print(f"⚠️ Если навык охотника не будет использован, это будет считаться отказом от стрельбы.")
                return None

            if hunter_action.metadata.get("shoot"):
                target = hunter_action.metadata.get("target")
                if target:
                    await self.moderator.announce(f"Охотник {hunter_agent.name} выстрелил и унес {target}")
                    return target
                else:
                    print(f"⚠️ Если охотник решил стрелять, но не указал цель, считается, что он сдался.")
                    return None
        
        return None
    
    def update_alive_players(self, dead_players: List[str]):
        """Обновить список выживших игроков"""
        for dead_name in dead_players:
            if dead_name:
                # Удалить из живого списка
                self.alive_players = [p for p in self.alive_players if p.name != dead_name]
                # Удален из всех фракций.
                self.werewolves = [p for p in self.werewolves if p.name != dead_name]
                self.villagers = [p for p in self.villagers if p.name != dead_name]
                self.seer = [p for p in self.seer if p.name != dead_name]
                self.witch = [p for p in self.witch if p.name != dead_name]
                self.hunter = [p for p in self.hunter if p.name != dead_name]
    
    async def day_phase(self, round_num: int):
        """дневная фаза"""
        await self.moderator.day_announcement(round_num)
        
        # стадия обсуждения
        async with MsgHub(
            self.alive_players,
            enable_auto_broadcast=True,
            announcement=await self.moderator.announce(
                f"Давайте начнем свободное обсуждение прямо сейчас. Выжившие игроки: {format_player_list(self.alive_players)}"
            ),
        ) as all_hub:
            # Каждый человек говорит в течение одного раунда
            await sequential_pipeline(self.alive_players)
            
            # этап голосования
            all_hub.set_auto_broadcast(False)
            vote_msgs = await fanout_pipeline(
                self.alive_players,
                await self.moderator.announce("Пожалуйста, голосуйте за игроков, которые будут исключены"),
                structured_model=get_vote_model_cn(self.alive_players),
                enable_gather=False,
            )
            
            # Статистическое голосование
            votes = {}
            for i, vote_msg in enumerate(vote_msgs):
                # Проверьте, имеет ли значение voice_msg значение None или существуют ли метаданные.
                if vote_msg is not None and hasattr(vote_msg, 'metadata') and vote_msg.metadata is not None:
                    votes[self.alive_players[i].name] = vote_msg.metadata.get("vote")
                else:
                    # Если результат недействителен, голос будет аннулирован по умолчанию.
                    print(f"⚠️ Голос пользователя {self.alive_players[i].name} недействителен и будет считаться отклоненным.")
                    votes[self.alive_players[i].name] = None
            
            voted_out, vote_count = majority_vote_cn(votes)
            await self.moderator.vote_result_announcement(voted_out, vote_count)
            
            return voted_out
    
    async def run_game(self):
        """Запустите основной цикл игры"""
        try:
            await self.setup_game()
            
            for round_num in range(1, MAX_GAME_ROUND + 1):
                print(f"\n🌙 === Игра начинается в раунде {round_num} ===")
                
                # ночная фаза
                await self.moderator.night_announcement(round_num)
                
                # оборотень убить
                killed_player = await self.werewolf_phase(round_num)
                
                # Проверка Провидца
                await self.seer_phase()
                
                # ведьма
                final_killed, poisoned_player = await self.witch_phase(killed_player)
                
                # Обновить мертвых игроков
                night_deaths = [p for p in [final_killed, poisoned_player] if p]
                self.update_alive_players(night_deaths)
                
                # объявление о смерти
                await self.moderator.death_announcement(night_deaths)
                
                # Проверьте условия победы
                winner = check_winning_cn(self.alive_players, self.roles)
                if winner:
                    await self.moderator.game_over_announcement(winner)
                    return
                
                # дневная фаза
                voted_out = await self.day_phase(round_num)
                
                # Навыки охотника
                hunter_shot = await self.hunter_phase(voted_out)
                
                # Обновить мертвых игроков
                day_deaths = [p for p in [voted_out, hunter_shot] if p]
                self.update_alive_players(day_deaths)
                
                # Проверьте условия победы
                winner = check_winning_cn(self.alive_players, self.roles)
                if winner:
                    await self.moderator.game_over_announcement(winner)
                    return
                
                print(f"Конец раунда {round_num}, выжившие игроки: {format_player_list(self.alive_players)}")
        
        except Exception as e:
            print(f"❌ Ошибка запуска игры: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """основная функция"""
    # Проверьте переменные среды
    if "DASHSCOPE_API_KEY" not in os.environ:
        print("❌ Установите переменную среды DASHSCOPE_API_KEY.")
        return
    
    print("🎮 Добро пожаловать в «Троецарствие оборотней»!")
    
    # Создать и запустить игру
    game = ThreeKingdomsWerewolfGame()
    await game.run_game()


if __name__ == "__main__":
    asyncio.run(main())
