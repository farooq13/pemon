import api from './api';

const notificationService = {
  // Fetch user notifications
  async getNotifications() {
    try {
      const response = await api.get('/core/notifications/');
      return response.data.results || response.data || [];
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
      return [];
    }
  },

  // Mark all notifications as read
  async markAllAsRead() {
    try {
      await api.post('/core/notifications/read-all/');
      return true;
    } catch (error) {
      console.error('Failed to mark all as read:', error);
      return false;
    }
  },

  // Mark single notification as read
  async markAsRead(id) {
    try {
      await api.post(`/core/notifications/${id}/read/`);
      return true;
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
      return false;
    }
  }
};

export default notificationService;
