import mongoose from 'mongoose';
const { Schema } = mongoose;

// 작업 스키마 (프로젝트의 서브다큐먼트)
const taskSchema = new Schema({
  id: {
    type: String,
    required: true,
    unique: true
  },
  agentType: {
    type: String,
    enum: ['designer', 'frontend', 'backend', 'ai_engineer'],
    required: true
  },
  description: {
    type: String,
    required: true
  },
  priority: {
    type: String,
    enum: ['high', 'medium', 'low'],
    default: 'medium'
  },
  deadline: {
    type: String,
    default: '미정'
  },
  status: {
    type: String,
    enum: ['pending', 'in_progress', 'completed', 'cancelled'],
    default: 'pending'
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  completedAt: {
    type: Date,
    default: null
  }
});

// 프로젝트 스키마
const projectSchema = new Schema({
  id: {
    type: String,
    required: true,
    unique: true
  },
  name: {
    type: String,
    required: true
  },
  description: {
    type: String,
    required: true
  },
  timeline: {
    type: String,
    default: '미정'
  },
  requirements: [{
    type: String
  }],
  status: {
    type: String,
    enum: ['planning', 'active', 'paused', 'completed'],
    default: 'active'
  },
  tasks: [taskSchema],
  completedTasks: [taskSchema],
  agentStatus: {
    designer: {
      type: String,
      enum: ['idle', 'working'],
      default: 'idle'
    },
    frontend: {
      type: String,
      enum: ['idle', 'working'],
      default: 'idle'
    },
    backend: {
      type: String,
      enum: ['idle', 'working'],
      default: 'idle'
    },
    ai_engineer: {
      type: String,
      enum: ['idle', 'working'],
      default: 'idle'
    }
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true
});

// 인덱스 설정
projectSchema.index({ id: 1 }, { unique: true });
projectSchema.index({ name: 1 });
projectSchema.index({ 'tasks.id': 1 });

const Project = mongoose.model('Project', projectSchema);

export default Project; 