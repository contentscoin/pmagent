import mongoose from 'mongoose';
const { Schema } = mongoose;

const mlModelSchema = new Schema({
  id: {
    type: String,
    required: true,
    unique: true
  },
  name: {
    type: String,
    required: true
  },
  type: {
    type: String,
    enum: ['classification', 'regression', 'clustering', 'reinforcement', 'nlp', 'computer_vision'],
    required: true
  },
  description: {
    type: String,
    required: true
  },
  architecture: {
    type: String,
    required: true
  },
  code: {
    type: String,
    required: true
  },
  parameters: {
    type: Schema.Types.Mixed
  },
  metrics: [{
    name: String,
    value: Schema.Types.Mixed,
    date: Date
  }],
  deploymentStatus: {
    type: String,
    enum: ['development', 'testing', 'staging', 'production'],
    default: 'development'
  },
  version: {
    type: String,
    default: '1.0.0'
  },
  projectId: {
    type: String,
    ref: 'Project'
  },
  createdBy: {
    type: String,
    default: 'ai_engineer_agent'
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
mlModelSchema.index({ id: 1 }, { unique: true });
mlModelSchema.index({ name: 1 });
mlModelSchema.index({ projectId: 1 });
mlModelSchema.index({ type: 1 });

const MLModel = mongoose.model('MLModel', mlModelSchema);

export default MLModel; 