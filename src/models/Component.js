import mongoose from 'mongoose';
const { Schema } = mongoose;

const componentSchema = new Schema({
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
  designId: {
    type: String,
    ref: 'Design'
  },
  platform: {
    type: String,
    enum: ['react', 'react-native', 'both'],
    required: true
  },
  code: {
    type: String,
    required: true
  },
  dependencies: [{
    name: String,
    version: String
  }],
  props: [{
    name: String,
    type: String,
    required: Boolean,
    default: Schema.Types.Mixed,
    description: String
  }],
  projectId: {
    type: String,
    ref: 'Project'
  },
  createdBy: {
    type: String,
    default: 'frontend_agent'
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
componentSchema.index({ id: 1 }, { unique: true });
componentSchema.index({ name: 1 });
componentSchema.index({ projectId: 1 });
componentSchema.index({ platform: 1 });

const Component = mongoose.model('Component', componentSchema);

export default Component; 