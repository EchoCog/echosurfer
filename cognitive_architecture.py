import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from enum import Enum
import logging
from pathlib import Path
import json
import datetime
from collections import deque
import time

class MemoryType(Enum):
    DECLARATIVE = "declarative"
    PROCEDURAL = "procedural"
    EPISODIC = "episodic"
    INTENTIONAL = "intentional"
    EMOTIONAL = "emotional"

@dataclass
class Memory:
    content: str
    memory_type: MemoryType
    timestamp: float
    associations: Set[str] = field(default_factory=set)
    emotional_valence: float = 0.0
    importance: float = 0.0
    context: Dict = field(default_factory=dict)

@dataclass
class Goal:
    description: str
    priority: float
    deadline: Optional[float]
    subgoals: List['Goal'] = field(default_factory=list)
    status: str = "pending"
    progress: float = 0.0
    context: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)

class PersonalityTrait:
    def __init__(self, name: str, base_value: float):
        self.name = name
        self.base_value = base_value
        self.current_value = base_value
        self.history = deque(maxlen=1000)
        
    def update(self, value: float, context: Dict):
        self.current_value = 0.7 * self.current_value + 0.3 * value
        self.history.append((datetime.datetime.now(), value, context))

class CognitiveArchitecture:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.memories: Dict[str, Memory] = {}
        self.goals: List[Goal] = []
        self.active_goals: List[Goal] = []
        self.personality_traits = {
            "curiosity": PersonalityTrait("curiosity", 0.8),
            "adaptability": PersonalityTrait("adaptability", 0.9),
            "persistence": PersonalityTrait("persistence", 0.7),
            "creativity": PersonalityTrait("creativity", 0.8),
            "analytical": PersonalityTrait("analytical", 0.85),
            "social": PersonalityTrait("social", 0.6)
        }
        
        # Initialize memory paths
        self.memory_path = Path.home() / '.deep_tree_echo' / 'memories'
        self.memory_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize performance tracking
        self.response_times = deque(maxlen=100)  # Store last 100 response times
        self.learning_timestamps = deque(maxlen=1000)  # Store last 1000 learning events
        self.memory_capacity = 10000  # Maximum memories to store
        
        # Initialize cognitive paths
        self.echo_dir = Path.home() / '.deep_tree_echo'
        self.cognitive_dir = self.echo_dir / 'cognitive'
        self.cognitive_dir.mkdir(parents=True, exist_ok=True)
        self.activity_file = self.cognitive_dir / 'activity.json'
        self.activities = []
        self._load_activities()
        
        # Load existing memories and goals
        self._load_state()
        
    def _load_state(self):
        """Load memories and goals from disk"""
        try:
            memory_file = self.memory_path / 'memories.json'
            if memory_file.exists():
                with open(memory_file) as f:
                    data = json.load(f)
                    for mem_data in data.get('memories', []):
                        self.memories[mem_data['id']] = Memory(**mem_data)
                    for goal_data in data.get('goals', []):
                        self.goals.append(Goal(**goal_data))
        except Exception as e:
            self.logger.error(f"Error loading state: {str(e)}")
            
    def _load_activities(self):
        """Load existing activities"""
        if self.activity_file.exists():
            try:
                with open(self.activity_file) as f:
                    self.activities = json.load(f)
            except:
                self.activities = []
                
    def _save_activities(self):
        """Save activities to file"""
        with open(self.activity_file, 'w') as f:
            json.dump(self.activities[-1000:], f)  # Keep last 1000 activities
            
    def _log_activity(self, description: str, context: Dict = None):
        """Log a cognitive activity"""
        try:
            activity_file = Path('activity_logs/cognitive/activity.json')
            
            # Read existing activities
            current = []
            if activity_file.exists():
                with open(activity_file) as f:
                    current = json.load(f)
            
            # Add new activity
            activity = {
                'time': time.time(),
                'description': description,
                'context': context or {}
            }
            current.append(activity)
            
            # Keep last 1000 activities
            if len(current) > 1000:
                current = current[-1000:]
            
            # Write back
            with open(activity_file, 'w') as f:
                json.dump(current, f)
                
        except Exception as e:
            self.logger.error(f"Error logging activity: {e}")
            
    def save_state(self):
        """Save current state to disk"""
        self._log_activity("Saving cognitive state")
        try:
            data = {
                'memories': [self._memory_to_dict(m) for m in self.memories.values()],
                'goals': [self._goal_to_dict(g) for g in self.goals]
            }
            with open(self.memory_path / 'memories.json', 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving state: {str(e)}")
            
    def generate_goals(self, context: Dict) -> List[Goal]:
        """Generate new goals based on current state and context"""
        self._log_activity(
            "Generating new goals",
            {'context': context}
        )
        goals = []
        
        # Factor in personality traits
        curiosity = self.personality_traits["curiosity"].current_value
        creativity = self.personality_traits["creativity"].current_value
        analytical = self.personality_traits["analytical"].current_value
        
        # Learning goals based on curiosity
        if curiosity > 0.6:
            knowledge_gaps = self._identify_knowledge_gaps()
            for gap in knowledge_gaps:
                goals.append(Goal(
                    description=f"Learn about: {gap}",
                    priority=curiosity * 0.8,
                    deadline=None,
                    context={"type": "learning", "area": gap}
                ))
                
        # System improvement goals based on analytical trait
        if analytical > 0.7:
            improvement_areas = self._analyze_system_performance()
            for area in improvement_areas:
                goals.append(Goal(
                    description=f"Improve system {area}",
                    priority=analytical * 0.9,
                    deadline=None,
                    context={"type": "improvement", "area": area}
                ))
                
        # Creative exploration goals
        if creativity > 0.6:
            exploration_ideas = self._generate_creative_ideas()
            for idea in exploration_ideas:
                goals.append(Goal(
                    description=f"Explore: {idea}",
                    priority=creativity * 0.7,
                    deadline=None,
                    context={"type": "exploration", "idea": idea}
                ))
                
        return goals
    
    def update_personality(self, experiences: List[Dict]):
        """Update personality traits based on experiences"""
        for exp in experiences:
            # Update curiosity based on learning experiences
            if exp.get('type') == 'learning':
                success = exp.get('success', 0.5)
                self.personality_traits["curiosity"].update(
                    success * 1.2,
                    {"experience": exp}
                )
                
            # Update adaptability based on change handling
            elif exp.get('type') == 'adaptation':
                effectiveness = exp.get('effectiveness', 0.5)
                self.personality_traits["adaptability"].update(
                    effectiveness,
                    {"experience": exp}
                )
                
            # Update persistence based on challenge handling
            elif exp.get('type') == 'challenge':
                resolution = exp.get('resolution', 0.5)
                self.personality_traits["persistence"].update(
                    resolution,
                    {"experience": exp}
                )
                
    def learn_from_experience(self, experience: Dict):
        """Learn from new experiences"""
        self._log_activity(
            "Learning from experience",
            {'experience': experience}
        )
        # Create memory
        memory = Memory(
            content=experience.get('description', ''),
            memory_type=MemoryType(experience.get('type', 'episodic')),
            timestamp=datetime.datetime.now().timestamp(),
            emotional_valence=experience.get('emotional_impact', 0.0),
            importance=experience.get('importance', 0.5),
            context=experience
        )
        
        # Store memory
        self.memories[str(len(self.memories))] = memory
        
        # Update personality based on experience
        self.update_personality([experience])
        
        # Generate new goals if needed
        if experience.get('importance', 0) > 0.7:
            new_goals = self.generate_goals({"trigger": experience})
            self.goals.extend(new_goals)
            
    def _identify_knowledge_gaps(self) -> List[str]:
        """Identify areas where knowledge is lacking"""
        # Analyze memories and identify areas with low coverage
        knowledge_areas = {}
        for memory in self.memories.values():
            if memory.memory_type == MemoryType.DECLARATIVE:
                area = memory.context.get('area', 'general')
                knowledge_areas[area] = knowledge_areas.get(area, 0) + 1
                
        # Find areas with low coverage
        gaps = []
        for area, count in knowledge_areas.items():
            if count < 5:  # Arbitrary threshold
                gaps.append(area)
                
        return gaps
    
    def _analyze_system_performance(self) -> List[str]:
        """Analyze system performance and identify areas for improvement"""
        # Example areas to monitor
        areas = ['memory_usage', 'response_time', 'learning_rate', 'goal_completion']
        improvements = []
        
        # Add areas that need improvement based on metrics
        for area in areas:
            if self._get_performance_metric(area) < 0.7:
                improvements.append(area)
                
        return improvements
    
    def _generate_creative_ideas(self) -> List[str]:
        """Generate new ideas for exploration"""
        # Combine existing knowledge in novel ways
        ideas = []
        memory_pairs = list(zip(
            self.memories.values(),
            self.memories.values()
        ))
        
        for mem1, mem2 in memory_pairs[:5]:  # Limit to prevent explosion
            if mem1.memory_type != mem2.memory_type:
                idea = f"Explore connection between {mem1.content} and {mem2.content}"
                ideas.append(idea)
                
        return ideas
    
    def _get_performance_metric(self, metric: str) -> float:
        """Get performance metric value based on actual system performance"""
        try:
            current_time = time.time()
            
            if metric == 'memory_usage':
                # Check memory utilization
                total_memories = len(self.memories)
                memory_capacity = getattr(self, 'memory_capacity', 10000)
                return min(1.0, total_memories / memory_capacity)
                
            elif metric == 'response_time':
                # Check average response time based on recent activity
                if hasattr(self, 'response_times') and self.response_times:
                    avg_response = sum(self.response_times[-10:]) / len(self.response_times[-10:])
                    # Normalize: 1.0 for < 1 second, 0.0 for > 10 seconds
                    return max(0.0, min(1.0, (10 - avg_response) / 9))
                return 0.8  # Default good response time
                
            elif metric == 'learning_rate':
                # Check how frequently new memories are being created
                if hasattr(self, 'learning_timestamps') and self.learning_timestamps:
                    recent_learning = [t for t in self.learning_timestamps if current_time - t < 3600]
                    # Normalize: 1.0 for 50+ new memories per hour
                    return min(1.0, len(recent_learning) / 50)
                return 0.6  # Default moderate learning rate
                
            elif metric == 'goal_completion':
                # Check goal completion rate
                completed_goals = [g for g in self.goals.values() if g.status == 'completed']
                total_goals = len(self.goals)
                if total_goals > 0:
                    return len(completed_goals) / total_goals
                return 0.5  # Default neutral completion rate
                
            else:
                # Unknown metric, return moderate performance
                self.logger.warning(f"Unknown performance metric: {metric}")
                return 0.7
                
        except Exception as e:
            self.logger.error(f"Error calculating performance metric {metric}: {e}")
            return 0.5  # Default fallback
    
    def _memory_to_dict(self, memory: Memory) -> Dict:
        """Convert memory to dictionary for storage"""
        return {
            'content': memory.content,
            'memory_type': memory.memory_type.value,
            'timestamp': memory.timestamp,
            'associations': list(memory.associations),
            'emotional_valence': memory.emotional_valence,
            'importance': memory.importance,
            'context': memory.context
        }
        
    def _goal_to_dict(self, goal: Goal) -> Dict:
        """Convert goal to dictionary for storage"""
        return {
            'description': goal.description,
            'priority': goal.priority,
            'deadline': goal.deadline,
            'status': goal.status,
            'progress': goal.progress,
            'context': goal.context,
            'dependencies': goal.dependencies,
            'subgoals': [self._goal_to_dict(g) for g in goal.subgoals]
        }

    def process_experience(self, experience: str, context: Dict = None) -> None:
        """Process a new experience and create memories"""
        start_time = time.time()
        
        try:
            self._log_activity(f"Processing experience: {experience}", context)
            
            # Create memory from experience
            memory_id = f"exp_{int(time.time() * 1000)}"
            memory = Memory(
                id=memory_id,
                content=experience,
                memory_type=MemoryType.EPISODIC,
                timestamp=time.time(),
                associations=set(),
                emotional_valence=context.get('emotional_valence', 0.0) if context else 0.0,
                importance=context.get('importance', 0.5) if context else 0.5,
                context=context or {}
            )
            
            # Store memory
            self.memories[memory_id] = memory
            
            # Track learning event
            self.learning_timestamps.append(time.time())
            
            # Find associations with existing memories
            self._create_associations(memory)
            
            # Update response time tracking
            response_time = time.time() - start_time
            self.response_times.append(response_time)
            
            self._log_activity("Experience processed successfully", 
                             {'memory_id': memory_id, 'response_time': response_time})
            
        except Exception as e:
            self.logger.error(f"Error processing experience: {e}")
            self._log_activity("Experience processing failed", {'error': str(e)})
            
    def _create_associations(self, new_memory: Memory):
        """Create associations between memories based on content similarity"""
        try:
            # Simple keyword-based association
            new_words = set(new_memory.content.lower().split())
            
            for memory_id, existing_memory in self.memories.items():
                if memory_id == new_memory.id:
                    continue
                    
                existing_words = set(existing_memory.content.lower().split())
                common_words = new_words.intersection(existing_words)
                
                # Create association if sufficient overlap
                if len(common_words) >= 2:
                    new_memory.associations.add(memory_id)
                    existing_memory.associations.add(new_memory.id)
                    
        except Exception as e:
            self.logger.error(f"Error creating associations: {e}")

    def generate_goal(self, description: str, priority: float = 0.5,
                   deadline: Optional[float] = None) -> Goal:
        """Generate a new goal"""
        try:
            self._log_activity(f"Generated goal: {description}", 
                             {'priority': priority, 'deadline': deadline})
            
            goal_id = f"goal_{int(time.time() * 1000)}"
            goal = Goal(
                id=goal_id,
                description=description,
                priority=priority,
                deadline=deadline,
                status='active',
                progress=0.0,
                context={},
                dependencies=[],
                subgoals=[]
            )
            
            self.goals.append(goal)
            
            # Add to active goals if priority is high enough
            if priority > 0.7:
                self.active_goals.append(goal)
            
            self._log_activity("Goal created successfully", {'goal_id': goal_id})
            return goal
            
        except Exception as e:
            self.logger.error(f"Error generating goal: {e}")
            # Return a minimal fallback goal
            return Goal(
                id=f"fallback_{int(time.time())}",
                description=description,
                priority=priority,
                deadline=deadline,
                status='error',
                progress=0.0,
                context={'error': str(e)},
                dependencies=[],
                subgoals=[]
            )

    def update_goal(self, goal: Goal, progress: float) -> None:
        """Update goal progress"""
        try:
            old_progress = goal.progress
            goal.progress = max(0.0, min(1.0, progress))  # Clamp to [0,1]
            
            # Update status based on progress
            if goal.progress >= 1.0:
                goal.status = 'completed'
                # Remove from active goals if present
                if goal in self.active_goals:
                    self.active_goals.remove(goal)
            elif goal.progress > 0.0:
                goal.status = 'in_progress'
            
            self._log_activity(f"Updated goal: {goal.description}", 
                             {'old_progress': old_progress, 'new_progress': goal.progress, 'status': goal.status})
            
        except Exception as e:
            self.logger.error(f"Error updating goal: {e}")
            self._log_activity("Goal update failed", {'error': str(e), 'goal': goal.description})
