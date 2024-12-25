import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import numpy as np
from collections import deque

@dataclass
class TreeNode:
    content: str
    echo_value: float = 0.0
    children: List['TreeNode'] = None
    parent: Optional['TreeNode'] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.metadata is None:
            self.metadata = {}

class DeepTreeEcho:
    def __init__(self, echo_threshold: float = 0.75, max_depth: int = 10):
        self.logger = logging.getLogger(__name__)
        self.echo_threshold = echo_threshold
        self.max_depth = max_depth
        self.root = None
    
    def create_tree(self, content: str) -> TreeNode:
        """Create initial tree structure from content"""
        self.root = TreeNode(content=content)
        return self.root
    
    def calculate_echo_value(self, node: TreeNode) -> float:
        """Calculate echo value for a node based on its content and children"""
        # Base echo from content length and complexity
        base_echo = len(node.content) / 1000  # Normalize by 1000 chars
        
        # Add complexity factor
        unique_chars = len(set(node.content))
        complexity_factor = unique_chars / 128  # Normalize by ASCII range
        
        # Calculate child echoes
        child_echo = 0
        if node.children:
            child_values = [child.echo_value for child in node.children]
            child_echo = np.mean(child_values) if child_values else 0
        
        # Combine factors with decay
        echo_value = (0.6 * base_echo + 0.3 * complexity_factor + 0.1 * child_echo)
        return min(1.0, echo_value)  # Normalize to [0,1]
    
    def propagate_echoes(self, node: TreeNode = None):
        """Propagate echo values through the tree"""
        if node is None:
            node = self.root
            
        # Calculate echo for current node
        node.echo_value = self.calculate_echo_value(node)
        
        # Propagate to children
        for child in node.children:
            self.propagate_echoes(child)
    
    def find_resonant_paths(self, threshold: float = None) -> List[List[TreeNode]]:
        """Find paths in the tree with high echo values"""
        if threshold is None:
            threshold = self.echo_threshold
            
        resonant_paths = []
        
        def dfs(node: TreeNode, current_path: List[TreeNode]):
            if len(current_path) > self.max_depth:
                return
                
            current_path.append(node)
            
            # Check if current path is resonant
            if node.echo_value >= threshold:
                resonant_paths.append(current_path.copy())
            
            # Continue search in children
            for child in node.children:
                dfs(child, current_path.copy())
        
        dfs(self.root, [])
        return resonant_paths
    
    def analyze_echo_patterns(self) -> Dict[str, Any]:
        """Analyze echo patterns in the tree"""
        if not self.root:
            return {}
            
        analysis = {
            'total_nodes': 0,
            'avg_echo': 0.0,
            'max_echo': 0.0,
            'resonant_nodes': 0,
            'depth': 0
        }
        
        # BFS to analyze tree
        queue = deque([(self.root, 0)])  # (node, depth)
        echo_values = []
        
        while queue:
            node, depth = queue.popleft()
            analysis['total_nodes'] += 1
            echo_values.append(node.echo_value)
            
            if node.echo_value >= self.echo_threshold:
                analysis['resonant_nodes'] += 1
                
            analysis['depth'] = max(analysis['depth'], depth)
            
            for child in node.children:
                queue.append((child, depth + 1))
        
        if echo_values:
            analysis['avg_echo'] = np.mean(echo_values)
            analysis['max_echo'] = max(echo_values)
            
        return analysis
    
    def inject_echo(self, source_node: TreeNode, target_node: TreeNode, strength: float = 0.5):
        """Inject echo from one node to another"""
        if 0 <= strength <= 1:
            # Calculate injection value
            injection = source_node.echo_value * strength
            
            # Apply injection with decay
            target_node.echo_value = min(1.0, target_node.echo_value + injection)
            
            # Propagate changes
            self.propagate_echoes(target_node)
        else:
            self.logger.warning("Echo injection strength must be between 0 and 1")
    
    def prune_weak_echoes(self, threshold: float = None):
        """Remove nodes with weak echo values"""
        if threshold is None:
            threshold = self.echo_threshold / 2  # Use half of normal threshold for pruning
            
        def should_keep(node: TreeNode) -> bool:
            return node.echo_value >= threshold
        
        def prune_recursive(node: TreeNode) -> bool:
            if not node:
                return False
                
            # First prune children
            node.children = [
                child for child in node.children 
                if prune_recursive(child)
            ]
            
            # Then check if this node should be kept
            return should_keep(node)
        
        # Start pruning from root
        if self.root and not prune_recursive(self.root):
            self.root = None
