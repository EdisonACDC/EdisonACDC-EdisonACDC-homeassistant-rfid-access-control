class RFIDAccessControlCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.users = [];
    this.selectedUser = null;
    this.showAddForm = false;
    this.showActionsForm = false;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('entity is required');
    }

    this.config = {
      entity: config.entity,
      title: config.title || 'RFID Access Control',
    };

    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.loadUsers();
  }

  async loadUsers() {
    if (!this._hass) return;

    try {
      // Get users from service (we'll implement a way to query them)
      // For now, we'll render the interface for managing users
      this.render();
    } catch (error) {
      console.error('Error loading users:', error);
    }
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          --primary-color: #2196F3;
          --accent-color: #FF9800;
          --success-color: #4CAF50;
          --danger-color: #F44336;
          --card-background: white;
          --text-primary: #212121;
          --text-secondary: #757575;
          --border-color: #BDBDBD;
        }

        .card {
          background: var(--card-background);
          border-radius: 4px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          padding: 24px;
          margin: 16px 0;
        }

        h1 {
          margin: 0 0 24px 0;
          color: var(--text-primary);
          font-size: 24px;
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .icon {
          width: 32px;
          height: 32px;
        }

        .button-group {
          display: flex;
          gap: 12px;
          margin-bottom: 24px;
          flex-wrap: wrap;
        }

        button {
          background: var(--primary-color);
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.3s;
        }

        button:hover {
          background: #1976D2;
          transform: translateY(-2px);
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }

        button.secondary {
          background: var(--accent-color);
        }

        button.secondary:hover {
          background: #F57C00;
        }

        button.danger {
          background: var(--danger-color);
        }

        button.danger:hover {
          background: #E53935;
        }

        .form-section {
          background: #F5F5F5;
          padding: 20px;
          border-radius: 4px;
          margin-bottom: 24px;
          display: ${this.showAddForm ? 'block' : 'none'};
        }

        .form-group {
          margin-bottom: 16px;
        }

        label {
          display: block;
          margin-bottom: 8px;
          color: var(--text-primary);
          font-weight: 500;
        }

        input, textarea {
          width: 100%;
          padding: 12px;
          border: 1px solid var(--border-color);
          border-radius: 4px;
          font-size: 14px;
          box-sizing: border-box;
        }

        input:focus, textarea:focus {
          outline: none;
          border-color: var(--primary-color);
          box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
        }

        .users-list {
          display: grid;
          gap: 12px;
        }

        .user-card {
          background: #F5F5F5;
          padding: 16px;
          border-radius: 4px;
          border-left: 4px solid var(--primary-color);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .user-info h3 {
          margin: 0 0 4px 0;
          color: var(--text-primary);
        }

        .user-info p {
          margin: 4px 0;
          color: var(--text-secondary);
          font-size: 12px;
        }

        .user-actions {
          display: flex;
          gap: 8px;
        }

        .user-actions button {
          padding: 8px 16px;
          font-size: 12px;
        }

        .status-badge {
          display: inline-block;
          padding: 4px 12px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 500;
          margin-top: 8px;
        }

        .status-enabled {
          background: var(--success-color);
          color: white;
        }

        .status-disabled {
          background: #BDBDBD;
          color: white;
        }

        .empty-state {
          text-align: center;
          padding: 40px 20px;
          color: var(--text-secondary);
        }

        .empty-state svg {
          width: 64px;
          height: 64px;
          margin-bottom: 16px;
          opacity: 0.5;
        }

        .actions-section {
          background: #F5F5F5;
          padding: 16px;
          border-radius: 4px;
          margin-top: 16px;
          display: ${this.showActionsForm && this.selectedUser ? 'block' : 'none'};
        }

        .actions-list {
          display: grid;
          gap: 8px;
          margin-top: 12px;
        }

        .action-item {
          background: white;
          padding: 12px;
          border-radius: 4px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border: 1px solid var(--border-color);
        }

        .close-btn {
          background: none;
          border: none;
          color: var(--text-secondary);
          font-size: 20px;
          cursor: pointer;
          padding: 0;
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .close-btn:hover {
          color: var(--text-primary);
          transform: scale(1.2);
        }

        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
        }

        @media (max-width: 600px) {
          .form-row {
            grid-template-columns: 1fr;
          }
          
          .user-card {
            flex-direction: column;
            align-items: flex-start;
          }

          .user-actions {
            width: 100%;
            margin-top: 12px;
          }
        }
      </style>

      <div class="card">
        <h1>
          <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
          </svg>
          ${this.config.title}
        </h1>

        <div class="button-group">
          <button onclick="${this._makeClickHandler('toggleAddForm')}">+ Add User</button>
          ${this.selectedUser ? `
            <button class="secondary" onclick="${this._makeClickHandler('toggleActionsForm')}">⚙️ Manage Actions</button>
          ` : ''}
        </div>

        <!-- Add User Form -->
        <div class="form-section">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h3>Add New User</h3>
            <button class="close-btn" onclick="${this._makeClickHandler('toggleAddForm')}">×</button>
          </div>

          <div class="form-group">
            <label>User ID (unique)*</label>
            <input type="text" id="userId" placeholder="e.g., mario_001" />
          </div>

          <div class="form-group">
            <label>Full Name*</label>
            <input type="text" id="userName" placeholder="e.g., Mario Rossi" />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>PIN (4-8 digits)</label>
              <input type="password" id="userPin" placeholder="1234" maxlength="8" />
            </div>
            <div class="form-group">
              <label>RFID Card ID</label>
              <input type="text" id="userRfid" placeholder="04A12B3C" />
            </div>
          </div>

          <button onclick="${this._makeClickHandler('submitAddUser')}">Create User</button>
        </div>

        <!-- Users List -->
        <h2>Registered Users</h2>
        ${this.users.length > 0 ? `
          <div class="users-list">
            ${this.users.map(user => `
              <div class="user-card">
                <div class="user-info">
                  <h3>${user.user_name}</h3>
                  <p>ID: ${user.user_id}</p>
                  <p>PIN: ${user.pin ? '****' : 'Not Set'} | RFID: ${user.rfid ? user.rfid : 'Not Set'}</p>
                  <p>Accesses: ${user.access_count} | Last: ${user.last_access ? new Date(user.last_access).toLocaleDateString() : 'Never'}</p>
                  <span class="status-badge ${user.enabled ? 'status-enabled' : 'status-disabled'}">
                    ${user.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <div class="user-actions">
                  <button onclick="${this._makeClickHandler('selectUser', user.user_id)}">Edit</button>
                  <button class="danger" onclick="${this._makeClickHandler('deleteUser', user.user_id)}">Delete</button>
                </div>
              </div>
            `).join('')}
          </div>
        ` : `
          <div class="empty-state">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>
            <p>No users registered yet</p>
          </div>
        `}

        <!-- Actions Management Form -->
        ${this.selectedUser ? `
          <div class="actions-section">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
              <h3>Manage Actions for ${this.selectedUser.user_name}</h3>
              <button class="close-btn" onclick="${this._makeClickHandler('toggleActionsForm')}">×</button>
            </div>

            <div class="form-group">
              <label>Action Name*</label>
              <input type="text" id="actionName" placeholder="e.g., Open Front Door" />
            </div>

            <div class="form-group">
              <label>Entity ID*</label>
              <input type="text" id="actionEntity" placeholder="light.living_room" />
            </div>

            <div class="form-group">
              <label>Service*</label>
              <input type="text" id="actionService" placeholder="light.turn_on" />
            </div>

            <div class="form-group">
              <label>Service Data (JSON)</label>
              <textarea id="actionData" placeholder='{"brightness": 255}' rows="3"></textarea>
            </div>

            <button onclick="${this._makeClickHandler('submitAddAction')}">Add Action</button>

            <div class="actions-list">
              ${this.selectedUser.actions.length > 0 ? this.selectedUser.actions.map((action, idx) => `
                <div class="action-item">
                  <div>
                    <strong>${action.action_name}</strong>
                    <p style="margin: 4px 0; font-size: 12px; color: var(--text-secondary);">
                      ${action.service} → ${action.entity_id}
                    </p>
                  </div>
                  <button class="danger" style="padding: 4px 8px;" onclick="${this._makeClickHandler('removeAction', idx)}">Remove</button>
                </div>
              `).join('') : '<p>No actions configured</p>'}
            </div>
          </div>
        ` : ''}
      </div>
    `;

    this.attachEventListeners();
  }

  _makeClickHandler(action, param) {
    return `(() => {
      const card = document.querySelector('rfid-access-control-card');
      card.${action}(${param ? `'${param}'` : ''});
    })()`;
  }

  attachEventListeners() {
    // Handlers are inline in render()
  }

  toggleAddForm() {
    this.showAddForm = !this.showAddForm;
    this.render();
  }

  toggleActionsForm() {
    this.showActionsForm = !this.showActionsForm;
    this.render();
  }

  selectUser(userId) {
    this.selectedUser = this.users.find(u => u.user_id === userId) || null;
    this.showActionsForm = false;
    this.render();
  }

  async submitAddUser() {
    const userId = this.shadowRoot.getElementById('userId')?.value;
    const userName = this.shadowRoot.getElementById('userName')?.value;
    const userPin = this.shadowRoot.getElementById('userPin')?.value;
    const userRfid = this.shadowRoot.getElementById('userRfid')?.value;

    if (!userId || !userName) {
      alert('User ID and Full Name are required');
      return;
    }

    try {
      await this._hass.callService('rfid_access_control', 'add_user', {
        user_id: userId,
        user_name: userName,
        user_pin: userPin,
        user_rfid: userRfid,
      });

      // Reload users
      await this.loadUsers();
      this.showAddForm = false;
      this.render();
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  }

  async deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user?')) return;

    try {
      await this._hass.callService('rfid_access_control', 'remove_user', {
        user_id: userId,
      });

      await this.loadUsers();
      if (this.selectedUser?.user_id === userId) {
        this.selectedUser = null;
      }
      this.render();
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  }

  async submitAddAction() {
    if (!this.selectedUser) return;

    const actionName = this.shadowRoot.getElementById('actionName')?.value;
    const actionEntity = this.shadowRoot.getElementById('actionEntity')?.value;
    const actionService = this.shadowRoot.getElementById('actionService')?.value;
    const actionDataStr = this.shadowRoot.getElementById('actionData')?.value;

    if (!actionName || !actionEntity || !actionService) {
      alert('Action Name, Entity ID, and Service are required');
      return;
    }

    let actionData = {};
    if (actionDataStr) {
      try {
        actionData = JSON.parse(actionDataStr);
      } catch (e) {
        alert('Invalid JSON in Service Data');
        return;
      }
    }

    try {
      await this._hass.callService('rfid_access_control', 'add_action', {
        user_id: this.selectedUser.user_id,
        action_name: actionName,
        action_entity: actionEntity,
        action_service: actionService,
        action_data: actionData,
      });

      await this.loadUsers();
      this.selectedUser = this.users.find(u => u.user_id === this.selectedUser.user_id) || null;
      this.render();
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  }

  async removeAction(actionIndex) {
    if (!this.selectedUser) return;

    const action = this.selectedUser.actions[actionIndex];
    if (!action) return;

    try {
      await this._hass.callService('rfid_access_control', 'remove_action', {
        user_id: this.selectedUser.user_id,
        action_name: action.action_name,
      });

      await this.loadUsers();
      this.selectedUser = this.users.find(u => u.user_id === this.selectedUser.user_id) || null;
      this.render();
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  }

  getCardSize() {
    return 4;
  }
}

customElements.define('rfid-access-control-card', RFIDAccessControlCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'rfid-access-control-card',
  name: 'RFID Access Control Card',
  description: 'Manage users, PINs, RFIDs and access control actions',
  preview: true,
});
