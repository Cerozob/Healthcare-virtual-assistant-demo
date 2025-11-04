/**
 * Session Manager
 * Handles session persistence and recovery for conversation continuity
 */

export interface SessionInfo {
  sessionId: string;
  createdAt: string;
  lastUsed: string;
  patientId?: string;
  messageCount: number;
}

export class SessionManager {
  private static readonly SESSION_KEY = 'healthcare-chat-session';
  private static readonly SESSION_HISTORY_KEY = 'healthcare-session-history';
  private static readonly MAX_SESSIONS = 10;
  private static readonly SESSION_TIMEOUT_HOURS = 24;

  /**
   * Generate a new session ID that meets AgentCore requirements (33+ chars)
   */
  static generateSessionId(): string {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substr(2, 9);
    const sessionId = `healthcare_${timestamp}_${random}`;
    
    // Ensure minimum length for AgentCore (33 characters)
    if (sessionId.length < 33) {
      const padding = '0'.repeat(33 - sessionId.length);
      return `${sessionId}${padding}`;
    }
    
    console.log(`🔑 Generated session ID: ${sessionId} (length: ${sessionId.length})`);
    return sessionId;
  }

  /**
   * Get current session or create a new one
   */
  static getCurrentSession(): SessionInfo {
    try {
      const stored = sessionStorage.getItem(this.SESSION_KEY);
      if (stored) {
        const session: SessionInfo = JSON.parse(stored);
        
        // Check if session is still valid (not expired)
        const lastUsed = new Date(session.lastUsed);
        const now = new Date();
        const hoursSinceLastUse = (now.getTime() - lastUsed.getTime()) / (1000 * 60 * 60);
        
        if (hoursSinceLastUse < this.SESSION_TIMEOUT_HOURS) {
          // Update last used time
          session.lastUsed = now.toISOString();
          this.saveSession(session);
          
          console.log(`🔄 Restored session: ${session.sessionId} (last used ${hoursSinceLastUse.toFixed(1)}h ago)`);
          return session;
        } else {
          console.log(`⏰ Session expired: ${session.sessionId} (${hoursSinceLastUse.toFixed(1)}h old)`);
          // Session expired, create new one
          sessionStorage.removeItem(this.SESSION_KEY);
        }
      }
    } catch (error) {
      console.warn('⚠️ Failed to restore session:', error);
    }

    // Create new session
    const newSession: SessionInfo = {
      sessionId: this.generateSessionId(),
      createdAt: new Date().toISOString(),
      lastUsed: new Date().toISOString(),
      messageCount: 0
    };

    this.saveSession(newSession);
    console.log(`🆕 Created new session: ${newSession.sessionId}`);
    
    return newSession;
  }

  /**
   * Save session to storage
   */
  static saveSession(session: SessionInfo): void {
    try {
      // Update last used time
      session.lastUsed = new Date().toISOString();
      
      // Save current session
      sessionStorage.setItem(this.SESSION_KEY, JSON.stringify(session));
      
      // Add to session history for recovery
      this.addToSessionHistory(session);
      
    } catch (error) {
      console.error('❌ Failed to save session:', error);
    }
  }

  /**
   * Update session with new information
   */
  static updateSession(updates: Partial<SessionInfo>): SessionInfo {
    const current = this.getCurrentSession();
    const updated = { ...current, ...updates };
    this.saveSession(updated);
    return updated;
  }

  /**
   * Start a new session (for patient changes, etc.)
   */
  static startNewSession(reason: string, patientId?: string): SessionInfo {
    const oldSession = this.getCurrentSession();
    console.log(`🔒 Starting new session (Reason: ${reason})`);
    
    // Archive old session
    if (oldSession.messageCount > 0) {
      this.archiveSession(oldSession, reason);
    }

    const newSession: SessionInfo = {
      sessionId: this.generateSessionId(),
      createdAt: new Date().toISOString(),
      lastUsed: new Date().toISOString(),
      patientId,
      messageCount: 0
    };

    this.saveSession(newSession);
    return newSession;
  }

  /**
   * Increment message count
   */
  static incrementMessageCount(): SessionInfo {
    const session = this.getCurrentSession();
    session.messageCount++;
    this.saveSession(session);
    return session;
  }

  /**
   * Add session to history for recovery
   */
  private static addToSessionHistory(session: SessionInfo): void {
    try {
      const historyJson = localStorage.getItem(this.SESSION_HISTORY_KEY);
      let history: SessionInfo[] = historyJson ? JSON.parse(historyJson) : [];
      
      // Remove existing entry for this session
      history = history.filter(s => s.sessionId !== session.sessionId);
      
      // Add current session
      history.unshift(session);
      
      // Keep only recent sessions
      history = history.slice(0, this.MAX_SESSIONS);
      
      localStorage.setItem(this.SESSION_HISTORY_KEY, JSON.stringify(history));
    } catch (error) {
      console.warn('⚠️ Failed to update session history:', error);
    }
  }

  /**
   * Archive a session when starting a new one
   */
  private static archiveSession(session: SessionInfo, reason: string): void {
    console.log(`📦 Archiving session ${session.sessionId} (${reason})`);
    
    try {
      const archiveKey = `healthcare-archived-session-${session.sessionId}`;
      const archiveData = {
        ...session,
        archivedAt: new Date().toISOString(),
        archiveReason: reason
      };
      
      // Store in localStorage for longer persistence
      localStorage.setItem(archiveKey, JSON.stringify(archiveData));
      
      // Clean up old archives (keep only last 5)
      this.cleanupArchivedSessions();
      
    } catch (error) {
      console.warn('⚠️ Failed to archive session:', error);
    }
  }

  /**
   * Clean up old archived sessions
   */
  private static cleanupArchivedSessions(): void {
    try {
      const archiveKeys = Object.keys(localStorage)
        .filter(key => key.startsWith('healthcare-archived-session-'))
        .sort()
        .reverse(); // Most recent first
      
      // Remove old archives (keep only 5 most recent)
      archiveKeys.slice(5).forEach(key => {
        localStorage.removeItem(key);
      });
      
    } catch (error) {
      console.warn('⚠️ Failed to cleanup archived sessions:', error);
    }
  }

  /**
   * Get session history for recovery
   */
  static getSessionHistory(): SessionInfo[] {
    try {
      const historyJson = localStorage.getItem(this.SESSION_HISTORY_KEY);
      return historyJson ? JSON.parse(historyJson) : [];
    } catch (error) {
      console.warn('⚠️ Failed to get session history:', error);
      return [];
    }
  }

  /**
   * Clear all session data (for logout, etc.)
   */
  static clearAllSessions(): void {
    try {
      // Clear current session
      sessionStorage.removeItem(this.SESSION_KEY);
      
      // Clear session history
      localStorage.removeItem(this.SESSION_HISTORY_KEY);
      
      // Clear archived sessions
      Object.keys(localStorage)
        .filter(key => key.startsWith('healthcare-archived-session-'))
        .forEach(key => localStorage.removeItem(key));
      
      console.log('🧹 All sessions cleared');
    } catch (error) {
      console.error('❌ Failed to clear sessions:', error);
    }
  }

  /**
   * Get session statistics
   */
  static getSessionStats(): {
    currentSession: SessionInfo | null;
    totalSessions: number;
    oldestSession: string | null;
    newestSession: string | null;
  } {
    const current = this.getCurrentSession();
    const history = this.getSessionHistory();
    
    return {
      currentSession: current,
      totalSessions: history.length,
      oldestSession: history.length > 0 ? history[history.length - 1].createdAt : null,
      newestSession: history.length > 0 ? history[0].createdAt : null
    };
  }
}
