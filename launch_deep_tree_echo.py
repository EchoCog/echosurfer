#!/usr/bin/env python3

import logging
import sys
import asyncio
import subprocess
from pathlib import Path
import os
import json
from deep_tree_echo import DeepTreeEcho
from browser_interface import DeepTreeEchoBrowser
from ml_system import MLSystem
from sensory_motor import SensoryMotor
from terminal_controller import TerminalController
from cognitive_architecture import CognitiveArchitecture
from personality_system import PersonalitySystem, Experience
from activity_regulation import ActivityRegulator, TaskPriority
from emergency_protocols import EmergencyProtocols

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('deep_tree_echo.log')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    try:
        # Initialize components
        logger.info("Initializing Deep Tree Echo components...")
        
        # Create necessary directories
        echo_dir = Path('activity_logs')
        echo_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize emergency protocols with explicit file creation
        emergency_dir = echo_dir / 'emergency'
        emergency_dir.mkdir(parents=True, exist_ok=True)
        emergency_file = emergency_dir / 'activity.json'
        if not emergency_file.exists():
            with open(emergency_file, 'w') as f:
                json.dump([], f)
        
        emergency = EmergencyProtocols()
        emergency._log_activity("System starting up")
        
        # Create other component directories
        for subdir in ['cognitive', 'sensory', 'ml', 'browser', 'terminal', 'personality']:
            component_dir = echo_dir / subdir
            component_dir.mkdir(parents=True, exist_ok=True)
            activity_file = component_dir / 'activity.json'
            if not activity_file.exists():
                with open(activity_file, 'w') as f:
                    json.dump([], f)
        
        # Initialize activity regulator
        activity = ActivityRegulator()
        
        # Initialize cognitive and personality systems
        cognitive = CognitiveArchitecture()
        personality = PersonalitySystem()
        
        # Initialize terminal controller
        terminal = TerminalController()
        terminal.start()
        
        # Set up sudo access
        if not terminal.verify_sudo_access():
            logger.info("Setting up sudo access...")
            emergency._log_activity("Setting up sudo access")
            if not terminal.setup_sudo_access():
                logger.error("Failed to set up sudo access")
                emergency._log_activity("Failed to set up sudo access", {"error": True})
                return
        
        # Start monitor interface in new terminal
        try:
            subprocess.Popen([
                'x-terminal-emulator', '-e',
                'python3', 'monitor_interface.py'
            ])
        except Exception as e:
            logger.error(f"Error starting monitor: {str(e)}")
        
        # Initialize ML system
        ml_system = MLSystem()
        ml_system._log_activity("ML System initialized")
        
        # Initialize browser interface
        browser = DeepTreeEchoBrowser()
        success = browser.init()
        if not success:
            logger.error("Failed to initialize browser interface")
            emergency._log_activity("Browser initialization failed", {"error": True})
            return
        
        # Initialize sensory-motor system
        sensory = SensoryMotor()
        sensory._log_activity("Sensory-motor system initialized")
        
        # Initialize core echo system
        echo = DeepTreeEcho()
        root = echo.create_tree("Deep Tree Echo Root")
        
        logger.info("Deep Tree Echo system initialized successfully")
        emergency._log_activity("System initialization complete")
        
        # Start health monitoring
        asyncio.create_task(emergency.monitor_health())
        
        # Initial goal generation
        initial_goals = cognitive.generate_goals({
            "system_state": "initialization",
            "personality": personality.personality.__dict__
        })
        
        logger.info("Initial goals generated: %s", 
                   [goal.description for goal in initial_goals])
        
        # Record initialization experience
        init_experience = Experience(
            type="system",
            description="System initialization complete",
            impact=0.7,
            context={
                "event": "initialization",
                "success": True
            }
        )
        personality.process_experience(init_experience)
        cognitive.learn_from_experience(init_experience.__dict__)
        
        # Update emergency protocols state
        emergency.update_state("operational")
        emergency.update_activity()
        
        # Schedule periodic tasks
        async def update_models():
            try:
                ml_system._log_activity("Starting model update cycle")
                await ml_system.update_models()
                ml_system._log_activity("Model update cycle complete")
            except Exception as e:
                emergency.log_error(f"Model update failed: {str(e)}")
            
        async def process_sensory():
            try:
                sensory._log_activity("Processing sensory input")
                sensory_data = sensory.process_input()
                if sensory_data:
                    # Get personality modulation
                    personality._log_activity("Calculating response modulation")
                    modulation = personality.get_response_modulation({
                        "sensory_input": True,
                        "data_type": sensory_data.get("type", "unknown")
                    })
                    
                    # Update echo patterns with personality influence
                    echo.propagate_echoes(modulation_factors=modulation)
                    patterns = echo.analyze_echo_patterns()
                    
                    # Learn from experience
                    experience = Experience(
                        type="sensory",
                        description="Processed sensory input",
                        impact=patterns.get("impact", 0.0),
                        context={
                            "patterns": patterns,
                            "modulation": modulation
                        }
                    )
                    personality.process_experience(experience)
                    cognitive.learn_from_experience(experience.__dict__)
                    
                    # Update emergency protocols
                    emergency.update_activity()
                    sensory._log_activity("Sensory processing complete", {"patterns": len(patterns)})
                    return patterns
                return None
            except Exception as e:
                emergency.log_error(f"Sensory processing failed: {str(e)}")
                return None
            
        async def check_goals():
            try:
                cognitive._log_activity("Checking goals")
                if cognitive.goals:
                    for goal in cognitive.goals:
                        if goal.status == "pending":
                            # Process goal
                            patterns = await process_sensory()
                            if patterns and patterns.get("matches_goal", False):
                                goal.status = "completed"
                                goal.progress = 1.0
                                cognitive._log_activity(f"Goal completed: {goal.description}")
                cognitive._log_activity("Goal check complete")
            except Exception as e:
                emergency.log_error(f"Goal checking failed: {str(e)}")
                
        async def save_state():
            try:
                emergency._log_activity("Starting state save")
                cognitive.save_state()
                personality.save_state()
                activity.save_state()
                emergency._log_activity("State save complete")
            except Exception as e:
                emergency.log_error(f"State saving failed: {str(e)}")
            
        # Schedule tasks with different priorities and intervals
        activity.schedule_task(
            "model_update",
            update_models,
            priority=TaskPriority.LOW,
            interval=3600,  # Every hour
            cpu_threshold=0.6
        )
        
        activity.schedule_task(
            "sensory_processing",
            process_sensory,
            priority=TaskPriority.HIGH,
            interval=0.1,  # Every 100ms
            cpu_threshold=0.8
        )
        
        activity.schedule_task(
            "goal_checking",
            check_goals,
            priority=TaskPriority.MEDIUM,
            interval=1.0,  # Every second
            cpu_threshold=0.7
        )
        
        activity.schedule_task(
            "state_saving",
            save_state,
            priority=TaskPriority.LOW,
            interval=300,  # Every 5 minutes
            cpu_threshold=0.5
        )
        
        # Run activity regulation
        try:
            emergency._log_activity("Starting main activity loop")
            await activity.run()
        except KeyboardInterrupt:
            logger.info("Shutting down Deep Tree Echo...")
            emergency._log_activity("System shutdown initiated")
            browser.close()
            terminal.cleanup()
            activity.cleanup()
            cognitive.save_state()
            personality.save_state()
            emergency.update_state("shutdown")
            emergency._log_activity("System shutdown complete")
            
    except Exception as e:
        logger.error("Error in Deep Tree Echo: %s", str(e))
        if emergency:
            emergency.log_error(f"Critical error in main loop: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
